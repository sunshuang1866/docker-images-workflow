# CI 失败分析报告

## 基本信息
- PR: #3077 — chore(accumulo): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 外部下载源网络不可达
- 新模式症状关键词: Failed to connect, Couldn't connect to server, curl: (28), archive.apache.org

## 根因分析

### 直接错误
```
#10 0.165   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#10 0.165                                  Dload  Upload   Total   Spent    Left  Speed
#10 0.165   0     0    0     0    0     0      0      0 --:--:--  0:02:13 --:--:--     0
#10 133.8 curl: (28) Failed to connect to archive.apache.org port 443 after 133684 ms: Couldn't connect to server
#10 133.9 tar (child): zookeeper.tar.gz: Cannot open: No such file or directory
#10 133.9 tar (child): Error is not recoverable: exiting now
#10 133.9 tar: Child returned status 2
#10 133.9 tar: Error is not recoverable: exiting now
#10 ERROR: process "/bin/sh -c curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz; ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile:16`（zookeeper 下载步骤）
- 失败原因: CI 构建环境（aarch64 runner）在执行 Dockerfile 第 4 步（安装 zookeeper）时，`curl` 尝试连接 `archive.apache.org` 超过 133 秒后超时失败（`curl: (28) Failed to connect to archive.apache.org port 443`），导致 zookeeper 二进制包下载失败，tar 因找不到文件而报错退出，整个 `RUN` 命令返回 exit code 2。

### 与 PR 变更的关联
- **直接关联**。PR 新增了完整的 `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile`（共 48 行），其中第 16-21 行为 zookeeper 下载安装步骤，正是 CI 构建失败的位置。
- 但失败**根因不是代码逻辑错误**，而是 CI 运行环境到 `archive.apache.org` 的网络连通性问题。该 URL（`https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`）路径格式和版本号均正确，属于基础设施层面的外部源不可达问题。
- 值得注意的是，日志中紧邻的上一步（yum install）也出现了非致命的 mirror 网络问题：`[MIRROR] xorg-x11-fonts-others: Curl error (92): Stream error in the HTTP/2 framing layer`，说明该 CI runner 节点的网络环境可能存在不稳定性，但该步通过其他镜像源重试后成功完成。

### 附加发现（非本次失败根因）
Dockerfile 中存在一个不一致问题——安装了 `java-11-openjdk-devel`，但 `JAVA_HOME` 指向了 `/usr/lib/jvm/java-17-openjdk`（该 JDK 未安装），会导致后续 `accumulo` 启动时找不到 Java。`entrypoint.sh` 中则写的是 `java-11-openjdk` 路径，两侧不一致。此问题与本次 CI 失败无关，但会在网络问题解决后暴露。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。CI runner 节点到 `archive.apache.org` 的网络超时可能是暂时的（CDN 波动或节点网络瞬断）。在不改变任何代码的情况下，重新触发 CI pipeline 可能直接通过。

### 方向 2（置信度: 低）
**切换 zookeeper 下载源**。如果 `archive.apache.org` 在 CI 环境中持续不可达，可将下载源从 `archive.apache.org`（Apache 归档站）替换为 `dlcdn.apache.org`（Apache CDN）或其他国内镜像源。需注意：`dlcdn.apache.org` 对旧版本支持可能有限（类似模式01），若 CDN 也无此版本则可尝试 `repo.huaweicloud.com` 等国内镜像。

## 需要进一步确认的点
1. CI runner（aarch64 节点）到 `archive.apache.org` 的网络连通性是否为持续问题——可手动 curl 该 URL 验证或查阅 CI 基础设施状态。
2. 若网络问题持续存在，需确认 `dlcdn.apache.org` 或其他镜像站是否托管了 Zookeeper 3.9.3 的 binary tarball。
3. Dockerfile 中 `JAVA_HOME` 路径不一致问题（`java-17-openjdk` vs `java-11-openjdk`）需在后续修复中一并解决，否则会在运行时阶段暴露。
