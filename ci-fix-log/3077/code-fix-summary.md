# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`（基础设施错误），根因是 CI runner 节点到 `archive.apache.org` 的网络连接超时，导致 zookeeper 二进制包下载失败，非代码逻辑错误。

## 修改的文件
无

## 修复逻辑
1. **CI 失败根因**：Dockerfile 第 16 行的 `curl -fSL -o zookeeper.tar.gz https://archive.apache.org/dist/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz` 在执行时，CI runner（aarch64 节点）到 `archive.apache.org:443` 的网络连接超时（耗时 133 秒后失败），随后 tar 因找不到下载文件而报错退出，导致整个 `RUN` 命令失败（exit code 2）。URL 路径和版本号均正确，属于外部源不可达的基础设施问题。

2. **推荐操作**：重新触发 CI pipeline（重试构建）。`archive.apache.org` 的网络波动通常是暂时的，在不改变任何代码的情况下，重新构建可能直接通过。

3. **备选方案**：若 `archive.apache.org` 在 CI 环境中持续不可达，可将第 16 行的下载源从 `archive.apache.org` 切换为 `dlcdn.apache.org` 或其他国内镜像源（如 `https://dlcdn.apache.org/zookeeper/zookeeper-3.9.3/apache-zookeeper-3.9.3-bin.tar.gz`），但需先验证镜像源是否托管了该版本的 binary tarball。

## 附加发现（非本次失败根因，需后续处理）
Dockerfile 中存在 JAVA_HOME 与已安装 JDK 版本不一致的问题：第 8 行安装的是 `java-11-openjdk-devel`，但第 13 行 `JAVA_HOME` 指向了 `/usr/lib/jvm/java-17-openjdk`（该 JDK 未安装）。此问题在网络连通性解决后会暴露，导致后续 accumulo 启动时找不到 Java。建议将 `JAVA_HOME` 修正为 `/usr/lib/jvm/java-11-openjdk` 或改为安装 `java-17-openjdk-devel`。

## 潜在风险
若直接切换下载源而不验证，存在目标镜像站不托管该版本 zookeeper 包的风险，导致同样的下载失败。建议优先重试构建，仅在 `archive.apache.org` 被确认为持续不可达时才切换源并验证。