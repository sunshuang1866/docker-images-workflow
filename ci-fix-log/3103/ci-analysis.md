# CI 失败分析报告

## 基本信息
- PR: #3103 — chore(kyuubi): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.534 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#9 134.9 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#9 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark &&     rm -f spark-${SPARK_VERSION}-bin-hadoop3.tgz" did not complete successfully: exit code: 4
------
Dockerfile:23
  22 |     # Download Spark (as mentioned in quick start for Spark engine)
  23 | >>> RUN wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
  24 | >>>     tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
  25 | >>>     mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark && \
  26 | >>>     rm -f spark-${SPARK_VERSION}-bin-hadoop3.tgz
------
ERROR: failed to solve: process "/bin/sh -c wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark &&     rm -f spark-${SPARK_VERSION}-bin-hadoop3.tgz" did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:23`
- 失败原因: CI 构建环境无法与 `archive.apache.org` 建立 TCP 连接（IPv4 全部 Connection timed out，IPv6 网络不可达），导致 wget 下载 Spark 3.4.2 压缩包超时失败（exit code: 4）。注意：Dockerfile 中 Kyuubi 本体从 `downloads.apache.org` 下载成功（#8 DONE 15.9s），但 Spark 从 `archive.apache.org` 下载失败。

### 与 PR 变更的关联
PR 新增了 `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`，该 Dockerfile 在第 23-26 行通过 `archive.apache.org` 下载 Spark 3.4.2。此 URL 的域名 `archive.apache.org` 在当前 CI 构建环境中不可达（已知问题，模式33），与 PR 代码质量无关，但 PR 直接引入了触发该问题的下载步骤。

## 修复方向

### 方向 1（置信度: 高）
将 Spark 下载源从 `archive.apache.org` 切换为 CI 环境可达的镜像站。参考模式33 历史案例（PR #3077 accumulo 将 Zookeeper 下载源从 `archive.apache.org` 更换为 `repo.huaweicloud.com`），将第 23 行的下载 URL 从 `https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz` 改为 `https://repo.huaweicloud.com/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz`。

### 方向 2（置信度: 中）
如果华为云镜像站的 Spark 镜像不完整，也可尝试 `https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz`（日志中 Kyuubi 从 `downloads.apache.org` 下载成功，说明该域名在 CI 环境中可达）。

## 需要进一步确认的点
1. 确认 `repo.huaweicloud.com/apache/spark/spark-3.4.2/` 路径下确实存在 `spark-3.4.2-bin-hadoop3.tgz` 文件。
2. 如果方向 1 不可用，依次验证 `downloads.apache.org` 或 `dlcdn.apache.org` 是否同时包含 Spark 3.4.2 制品。

## 修复验证要求
修复后需触发 CI 重新构建，确认：
- `wget` 能成功下载 Spark 3.4.2 压缩包
- Docker 镜像构建完整通过
- 新指定的镜像站 URL 可稳定访问（非临时可达）
