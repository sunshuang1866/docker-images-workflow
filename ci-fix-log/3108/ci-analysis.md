# CI 失败分析报告

## 基本信息
- PR: #3108 — chore(mesos): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Apache CDN 网络不可达
- 新模式症状关键词: Connection timed out, downloads.apache.org, wget, Network is unreachable, exit code: 4

## 根因分析

### 直接错误
```
#12 0.110 Connecting to downloads.apache.org (downloads.apache.org)|95.216.224.44|:443... failed: Connection timed out.
#12 136.3 Connecting to downloads.apache.org (downloads.apache.org)|88.99.208.237|:443... failed: Connection timed out.
#12 271.5 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f8:10a:39da::2|:443... failed: Network is unreachable.
#12 271.5 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f9:2b:1cc2::2|:443... failed: Network is unreachable.
#12 ERROR: process "/bin/sh -c wget https://downloads.apache.org/mesos/${VERSION}/mesos-${VERSION}.tar.gz && tar -zxf mesos-${VERSION}.tar.gz" did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile:42`（`wget` 步骤）
- 失败原因: CI 构建节点无法连接 `downloads.apache.org` 的所有 IPv4/IPv6 地址（95.216.224.44、88.99.208.237 超时；IPv6 地址网络不可达），导致 wget 下载 Mesos 1.11.0 源码包失败（exit code 4）。

### 与 PR 变更的关联
与 PR 变更**无关**。该 PR 新增了 mesos 1.11.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，Dockerfile 中引用的下载 URL `https://downloads.apache.org/mesos/1.11.0/mesos-1.11.0.tar.gz` 格式正确。同时，同一构建中的前一步（Python 2.7.18 构建步骤，step #11）成功从 `www.openssl.org` 和 `www.python.org` 完成下载，证明 CI 节点具备基本出网能力，问题仅出现在 Apache CDN 域名 `downloads.apache.org` 的连接上。故障属于 CI 基础设施网络层面的偶发性问题。

## 修复方向

### 方向 1（置信度: 中）
**直接重试触发 CI 重新构建**。由于前一步 Python/OpenSSL 下载正常，该问题大概率是 `downloads.apache.org` CDN 节点在 CI 构建时刻出现的临时网络故障。重新触发 Pipeline 有很大概率通过。

### 方向 2（置信度: 低）
**更换下载源**。若重试后仍然失败，说明 CI 构建网络对 `downloads.apache.org` 存在持续性阻断。可将下载源从 `downloads.apache.org` 切换为 Apache 归档站 `archive.apache.org`（URL: `https://archive.apache.org/dist/mesos/${VERSION}/mesos-${VERSION}.tar.gz`），该域名通常具有更好的全网可达性。

## 需要进一步确认的点
1. 重新触发 Pipeline 后是否仍然失败——如果重试通过，则确认为临时网络抖动，无需修改代码。
2. CI 构建节点所在网络环境对 `downloads.apache.org` 各 IP 的连通性（可能需要运维排查防火墙/代理策略）。
3. `archive.apache.org` 域名在 CI 环境中是否可达（可用作备选下载源）。
