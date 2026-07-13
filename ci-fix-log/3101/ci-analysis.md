# CI 失败分析报告

## 基本信息
- PR: #3101 — chore(knox): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Apache下载源网络不可达
- 新模式症状关键词: Connection timed out, downloads.apache.org, Network is unreachable, wget, exit code: 4

## 根因分析

### 直接错误
```
#10 [5/9] RUN wget https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip &&     unzip knox-2.1.0.zip &&     rm -f knox-2.1.0.zip
#10 0.089 Resolving downloads.apache.org (downloads.apache.org)... 95.216.224.44, 88.99.208.237, 2a01:4f8:10a:39da::2, ...
#10 0.090 Connecting to downloads.apache.org (downloads.apache.org)|95.216.224.44|:443... failed: Connection timed out.
#10 135.8 Connecting to downloads.apache.org (downloads.apache.org)|88.99.208.237|:443... failed: Connection timed out.
#10 270.9 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f8:10a:39da::2|:443... failed: Network is unreachable.
#10 270.9 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f9:2b:1cc2::2|:443... failed: Network is unreachable.
#10 ERROR: process "/bin/sh -c wget https://downloads.apache.org/knox/${VERSION}/knox-${VERSION}.zip &&     unzip knox-${VERSION}.zip &&     rm -f knox-${VERSION}.zip" did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/knox/2.1.0/24.03-lts-sp4/Dockerfile:21-23`（wget 下载 knox zip 步骤）
- 失败原因: CI runner 无法通过 HTTPS(443) 连接到 `downloads.apache.org` 的所有解析 IP（2 个 IPv4 地址均 Connection timed out，2 个 IPv6 地址均 Network is unreachable），导致 `wget` 下载 Knox 2.1.0 安装包失败（exit code 4 = Network failure）。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了一个 Dockerfile（`Bigdata/knox/2.1.0/24.03-lts-sp4/Dockerfile`）及相关文档/元数据条目，Dockerfile 内容本身无语法或逻辑错误。失败的直接原因是 CI 构建节点到 `downloads.apache.org` 的网络路由不通，属于 CI 基础设施层面的网络连通性问题。证据：
1. 同一构建中，`dlcdn.apache.org`（Hadoop 下载）连通正常，说明 CI runner 具备基本外网访问能力。
2. `downloads.apache.org` 的 4 个 IP 全部不可达（IPv4 超时 + IPv6 不可达），指向该特定主机/网段的路由阻断或防火墙拦截，而非 PR 代码问题。
3. 现有的 SP2 Dockerfile 使用相同 URL 模式，若在同一 CI runner 上构建应同样失败，进一步说明这是网络环境/节点相关的问题。

## 修复方向

### 方向 1（置信度: 中）
**更换下载源为 Apache Archive。** `downloads.apache.org` 是 Apache 的镜像重定向服务，在某些 CI 网络环境下可能被防火墙拦截或路由不通。将 Knox 的下载 URL 从 `https://downloads.apache.org/knox/${VERSION}/knox-${VERSION}.zip` 替换为 `https://archive.apache.org/dist/knox/${VERSION}/knox-${VERSION}.zip`，`archive.apache.org` 作为归档站通常具有更好的 CI 环境可达性。

### 方向 2（置信度: 低）
**重试构建。** 如果 `downloads.apache.org` 的不可达仅是临时性网络波动（如上游路由故障、DNS 解析异常），稍后重试 CI 构建可能自然通过。但考虑到 IPv4 和 IPv6 共 4 个地址全部不可达（而非部分可达），更倾向于网络策略层面的阻断而非临时故障，重试成功概率较低。

## 需要进一步确认的点
1. **确认 `downloads.apache.org` 在 CI 构建节点上的可达性**：在 CI runner 上手动执行 `curl -v https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip` 或 `wget --timeout=30 https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip`，确认是否为持续性的网络阻断。
2. **对比同一 runner 上其他 Apache 主机**：已验证 `dlcdn.apache.org` 可达，需确认 `archive.apache.org` 是否同样可达。
3. **检查现有 SP2 Dockerfile 的同源构建状态**：`Bigdata/knox/2.1.0/24.03-lts-sp2/Dockerfile` 使用相同的 `downloads.apache.org` URL，若该构建在当前 CI 环境中也失败，则确认为普遍性网络问题；若成功，则说明此 fail 为临时波动。

## 修复验证要求
若采用方向 1（更换为 `archive.apache.org`），code-fixer 需在修改前手动验证：
- `https://archive.apache.org/dist/knox/2.1.0/knox-2.1.0.zip` 确实存在且可下载（HTTP 200）。
- 同样需要对 SP2 Dockerfile 做一致性检查，确认 SP2 版本的 knox 包在 `archive.apache.org` 上同样可用，避免后续 SP2 构建遇到相同问题。
