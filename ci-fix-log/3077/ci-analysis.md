# CI 失败分析报告

## 基本信息
- PR: #3077 — chore(accumulo): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33（近似匹配）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#10 133.8 curl: (28) Failed to connect to archive.apache.org port 443 after 133684 ms: Couldn't connect to server
#10 133.9 tar (child): zookeeper.tar.gz: Cannot open: No such file or directory
#10 133.9 tar (child): Error is not recoverable: exiting now
#10 133.9 tar: Child returned status 2
#10 133.9 tar: Error is not recoverable: exiting now
#10 ERROR: process "/bin/sh -c curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz; ..." did not complete successfully: exit code: 2
------
Dockerfile:16
```

### 根因定位
- 失败位置: `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile:16`
- 失败原因: CI 构建环境（aarch64 runner）无法与 `archive.apache.org` 建立 TCP 连接，curl 在约 133 秒后超时（exit code 28），导致 zookeeper 压缩包下载失败，后续 tar 解压因文件不存在而报错。yum 安装步骤（step #9）已成功完成，镜像仓库 `repo.openeuler.org` 可达（仅有非致命的 HTTP/2 流错误警告）。

### 与 PR 变更的关联
PR 新增的 Dockerfile 在 zookeeper 安装步骤（第 16 行）中将下载源硬编码为 `https://archive.apache.org/dist/zookeeper/...`。此 URL 本身语法正确、对应 zookeeper 3.9.3 的合法制品路径，但 CI 的 aarch64 构建节点网络环境无法访问 `archive.apache.org`。这与 PR 的代码逻辑无关——同样的 URL 在本地/其他网络环境中可以正常下载。该问题属于 CI 网络可达性限制，可通过更换下载源（如 `dlcdn.apache.org` 或国内镜像站）绕过。

## 修复方向

### 方向 1（置信度: 高）
将 Zookeeper 的下载源从 `archive.apache.org` 更换为 CI 环境可达的替代源。参考模式33的历史修复经验，可将下载 URL 切换为 Apache CDN（`dlcdn.apache.org`）或国内镜像站（如 `repo.huaweicloud.com/apache/zookeeper/`）。同时建议一并检查 Dockerfile 中 Hadoop 和 Accumulo 的下载源（当前使用 `dlcdn.apache.org`），确认它们在同一 CI 环境中可达。

### 方向 2（置信度: 低，补充观察）
Dockerfile 存在 JAVA_HOME 不一致：通过 `yum install java-11-openjdk-devel` 安装 Java 11，但 `ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk` 硬编码为 Java 17 路径；而 `hadoop-env.sh` 中 `export JAVA_HOME=/usr/lib/jvm/java-11-openjdk` 又指向 Java 11。当前构建失败与此无关，但会在运行时造成 Java 版本混乱，建议在修复主要问题后一并修正（将 JAVA_HOME 统一为 `/usr/lib/jvm/java-11-openjdk` 或切换为安装 java-17-openjdk-devel）。

## 需要进一步确认的点
1. 确认 CI aarch64 runner 的网络环境中 `dlcdn.apache.org` 或 `repo.huaweicloud.com` 是否可达（可通过在 Dockerfile 中加入 `RUN curl -I <url>` 探测）。
2. 确认 Hadoop 和 Accumulo 的下载 URL（`dlcdn.apache.org`）在本次构建失败前未被执行到，后续构建是否也会因相同网络问题失败。
3. Zookeeper 3.9.3 在 `dlcdn.apache.org` 上是否提供（Apache CDN 主要托管当前发行版，历史版本可能仅在 archive 有，需验证可用性后再切换）。

## 修复验证要求
修复后需确认 Docker 镜像构建能通过 zookeeper 下载步骤（step 4/10 或对应序号），且后续 Hadoop、Accumulo 下载步骤也均能成功。若切换为华为云镜像站，需确认对应路径格式（`repo.huaweicloud.com/apache/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`）与 archive 路径一致，制品确实存在。
