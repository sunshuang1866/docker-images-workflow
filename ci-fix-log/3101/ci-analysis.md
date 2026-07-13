# CI 失败分析报告

## 基本信息
- PR: #3101 — chore(knox): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Apache 镜像站网络不通
- 新模式症状关键词: Connection timed out, download.apache.org, wget, exit code: 4

## 根因分析

### 直接错误

```
#10 [5/9] RUN wget https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip && ...
#10 0.089 Resolving downloads.apache.org (downloads.apache.org)... 95.216.224.44, 88.99.208.237, 2a01:4f8:10a:39da::2, ...
#10 0.090 Connecting to downloads.apache.org (downloads.apache.org)|95.216.224.44|:443... failed: Connection timed out.
#10 135.8 Connecting to downloads.apache.org (downloads.apache.org)|88.99.208.237|:443... failed: Connection timed out.
#10 270.9 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f8:10a:39da::2|:443... failed: Network is unreachable.
#10 270.9 Connecting to downloads.apache.org (downloads.apache.org)|2a01:4f9:2b:1cc2::2|:443... failed: Network is unreachable.
#10 ERROR: process "/bin/sh -c wget https://downloads.apache.org/knox/${VERSION}/knox-${VERSION}.zip && ..." did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/knox/2.1.0/24.03-lts-sp4/Dockerfile:21`（wget 下载 Knox 步骤）
- 失败原因: CI 构建环境无法与 `downloads.apache.org` 建立 TCP 连接（所有 IPv4 地址均 Connection timed out，IPv6 地址 Network is unreachable），导致 wget 下载 Knox 2.1.0 压缩包失败（exit code: 4）。

### 与 PR 变更的关联
PR 新增了 Knox 2.1.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，构建过程中第 5/9 步（`wget https://downloads.apache.org/knox/2.1.0/knox-2.1.0.zip`）因网络不通而失败。PR 的 Dockerfile 语法本身无误（前序步骤均成功，包括 `dnf install` 装完 261 个包、Hadoop 928M 从 `dlcdn.apache.org` 成功下载）。本次失败与 PR 代码变更无关，属于 CI 基础设施网络问题。

值得注意的是，同一构建中步骤 #8 从 `dlcdn.apache.org` 下载 Hadoop 成功（耗时 ~39s），而步骤 #10 从 `downloads.apache.org` 下载 Knox 失败。说明 CI 环境可正常访问 `dlcdn.apache.org`，但无法访问 `downloads.apache.org`——后者可能被 CI 网络防火墙阻断或其服务本身不可用。

## 修复方向

### 方向 1（置信度: 高）
将 Knox 的下载源从 `downloads.apache.org` 更换为 `dlcdn.apache.org`（Apache CDN 直连地址），该地址在同一次构建中已被验证可达。Knox 2.1.0 的制品同样托管在 CDN 上，URL 格式为 `https://dlcdn.apache.org/knox/${VERSION}/knox-${VERSION}.zip`。

### 方向 2（置信度: 中）
若 CDN 上的 Knox 历史版本也被清理（类似模式01中 Maven 的情况），可改用 `archive.apache.org/dist/knox/${VERSION}/knox-${VERSION}.zip` 作为下载源，Archive 站点通常保留所有历史版本。

### 方向 3（置信度: 低）
等待 CI 网络恢复后重试构建。若 `downloads.apache.org` 的不可达是临时性故障，重试即可通过。但从可靠性角度，换用已验证可达的 CDN 地址更为稳妥。

## 需要进一步确认的点
1. 确认 `https://dlcdn.apache.org/knox/2.1.0/knox-2.1.0.zip` 在 CDN 上是否可用（是否存在、是否返回 404）。若 CDN 不托管 Knox，需另选镜像源。
2. 确认 CI 构建环境对 `downloads.apache.org` 的网络限制是临时性的还是永久性的（如防火墙规则）。
