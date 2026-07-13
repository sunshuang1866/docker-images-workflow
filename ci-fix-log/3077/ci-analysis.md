# CI 失败分析报告

## 基本信息
- PR: #3077 — chore(accumulo): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 网络连接超时
- 新模式症状关键词: curl: (28), Failed to connect, archive.apache.org, Couldn't connect to server, timeout

## 根因分析

### 直接错误
```
#10 [ 4/10] RUN curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz; ...
#10 0.165   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#10 0.165                                  Dload  Upload   Total   Spent    Left  Speed
#10 133.8 curl: (28) Failed to connect to archive.apache.org port 443 after 133684 ms: Couldn't connect to server
#10 133.9 tar (child): zookeeper.tar.gz: Cannot open: No such file or directory
#10 133.9 tar (child): Error is not recoverable: exiting now
#10 133.9 tar: Child returned status 2
#10 133.9 tar: Error is not recoverable: exiting now
#10 ERROR: process "/bin/sh -c curl -fSL -o zookeeper.tar.gz ..." did not complete successfully: exit code: 2
------
Dockerfile:16
```

### 根因定位
- 失败位置: `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile:16`
- 失败原因: CI 构建环境无法通过 HTTPS 连接到 `archive.apache.org`（curl 错误码 28，操作超时），导致 Zookeeper 二进制包下载失败。tar 随后因 `.tar.gz` 文件不存在而报错退出。

### 与 PR 变更的关联
PR 新增了完整的 `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile`，其中第 16 行的 `RUN` 步骤通过 `curl` 从 `archive.apache.org` 下载 Zookeeper 3.9.3。该 URL 对目标构建环境不可达，导致 Docker 构建在步骤 4/10 失败。此外，Dockerfile 中后续的 Hadoop（`dlcdn.apache.org`）和 Accumulo（`dlcdn.apache.org`）下载步骤尚未执行即已失败，若 `dlcdn.apache.org` 在当前 CI 环境中也不可达，则修复 Zookeeper 下载后仍可能继续失败。

> **附注**：构建步骤 #9（yum install）中也出现了一次 repo 镜像警告——`[MIRROR] xorg-x11-fonts-others...: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/...`，但 yum 从其他镜像重试后成功安装了全部 96 个包并输出 `Complete!`，该警告不是根因。

## 修复方向

### 方向 1（置信度: 中）
将 Zookeeper 的下载源从 `archive.apache.org` 替换为 CI 环境可访问的镜像站。常见的替代方案包括：
- 华为云镜像站：`https://repo.huaweicloud.com/apache/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`
- 清华镜像站：`https://mirrors.tuna.tsinghua.edu.cn/apache/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`
- 阿里云镜像站：`https://mirrors.aliyun.com/apache/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`

> ⚠️ 同时需要评估 Dockerfile 中 Hadoop 和 Accumulo 的 `dlcdn.apache.org` 下载源是否也需要替换。参照历史模式 01，`dlcdn.apache.org` 仅托管最新版本，旧版本可能 404。Hadoop 3.4.1 和 Accumulo 3.0.0 当前是否仍在 CDN 上可用需要验证；若不可用，也应一并换为归档站或镜像站。

### 方向 2（置信度: 低）
若 `archive.apache.org` 在 CI 环境中实际上可达但临时性故障（例如 DNS 解析问题或间歇性网络波动），则最简单的修复是在 `curl` 命令中添加 `--retry 3 --retry-delay 10` 参数以增加容错性。但由于超时长达 133 秒后仍失败，此方向可能性较低。

## 需要进一步确认的点

1. **确认 CI 环境网络限制**：验证 CI runner 是否可以正常访问 `archive.apache.org`。如果该域名在 CI 环境中被永久屏蔽或不可达，则必须换用镜像站（方向 1）。
2. **验证 `dlcdn.apache.org` 可访问性**：确认 Hadoop 3.4.1 和 Accumulo 3.0.0 在 `dlcdn.apache.org` 上的制品是否仍然可用（HTTP 200），以及 CI 环境是否能连接该域名。参照模式 01，CDN 可能已下架旧版本。
3. **确认镜像站上 Zookeeper 3.9.3 制品的可用性**：在选定替换镜像站后，需确认该镜像站确实托管了 `apache-zookeeper-3.9.3-bin.tar.gz`。
4. **检查同类 Dockerfile 的下载方式**：查看仓库中其他使用 openEuler 24.03-lts-sp4 的 Dockerfile（尤其是同属 `Bigdata/` 场景的），看它们使用何种下载源和网络配置，确保与现有实践一致。

## 修复验证要求

若修复方向 1 被采纳（将 Zookeeper 下载源从 `archive.apache.org` 更换为镜像站），code-fixer 必须在提交前：
- 验证所选镜像站上 `apache-zookeeper-3.9.3-bin.tar.gz` 确实存在且可下载（HTTP 200）。
- 验证该 Dockerfile 中 Hadoop 和 Accumulo 的 `dlcdn.apache.org` URL 是否也需要替换（同样检查制品是否存在）。
