# 修复摘要

## 修复的问题
将 Zookeeper 下载源从 `archive.apache.org` 更换为 `repo.huaweicloud.com`（华为云镜像站），解决 CI aarch64 构建节点无法连接 `archive.apache.org` 导致 curl 超时的问题。

## 修改的文件
- `Bigdata/accumulo/3.0.0/24.03-lts-sp4/Dockerfile`: 第 16 行 Zookeeper 下载 URL 从 `https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz` 改为 `https://repo.huaweicloud.com/apache/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`

## 修复逻辑
CI 分析报告指出根因是 CI 的 aarch64 runner 无法与 `archive.apache.org` 建立 TCP 连接（curl exit code 28），属于基础设施网络限制。`dlcdn.apache.org` 不托管 Zookeeper 3.9.3 版本（仅托管 3.7.2、3.8.6、3.9.5），因此切换为构建环境中可达的华为云镜像站。经验证，华为云镜像站 `https://repo.huaweicloud.com/apache/zookeeper/zookeeper-3.9.3/` 路径下制品存在且可下载（HTTP 200，文件大小超过 5MB）。

## 潜在风险
- Hadoop（`dlcdn.apache.org`）和 Accumulo（`dlcdn.apache.org`）的下载源仍在同上 Dockerfile 的后续步骤中使用，若 CI 环境同样无法访问 `dlcdn.apache.org`，后续构建步骤也可能失败，但目前无此现象。
- Dockerfile 第 13 行 `ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk` 与第 8 行安装的 `java-11-openjdk-devel` 不一致（hadoop-env.sh 中正确指向 `/usr/lib/jvm/java-11-openjdk`），此问题与当前构建失败无关，但可能导致运行时 Java 版本混乱，建议后续单独修复。