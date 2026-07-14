# 修复摘要

## 修复的问题
CI 构建时 `archive.apache.org` 不可达，导致 Spark 3.4.2 下载超时失败。

## 修改的文件
- `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`: 将 Spark 下载源从 `archive.apache.org` 切换为 `repo.huaweicloud.com`（第 23 行）

## 修复逻辑
分析报告指出这是一个 `infra-error`（模式33）：CI 构建环境无法与 `archive.apache.org` 建立 TCP 连接，但 Kyuubi 本体从 `dlcdn.apache.org` 下载成功说明网络本身正常。按照 PR #3077 的修复模式（Zookeeper 下载源从 `archive.apache.org` 更换到 `repo.huaweicloud.com`），将 Spark 下载 URL 从 `https://archive.apache.org/dist/spark/...` 改为 `https://repo.huaweicloud.com/apache/spark/...`。已从上游验证 `https://repo.huaweicloud.com/apache/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz` 文件存在且可访问。`dlcdn.apache.org` 和 `downloads.apache.org` 均不托管 Spark 3.4.2 制品（返回 404），故华为云镜像站是最佳选择。

## 潜在风险
无。其他 Kyuubi 版本（1.10.0、1.10.2、1.11.1-sp3）的 Dockerfile 仍使用 `archive.apache.org`，但这些文件不在本次 PR 变更范围内，按最小化原则不做修改。