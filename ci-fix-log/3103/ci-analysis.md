# CI 失败分析报告

## 基本信息
- PR: #3103 — chore(kyuubi): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
#9 0.108 --2026-07-14 08:01:10--  https://archive.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz
#9 0.534 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#9 134.9 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#9 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark &&     rm -f spark-${SPARK_VERSION}-bin-hadoop3.tgz" did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:23`（wget 下载 Spark 步骤）
- 失败原因: CI 构建环境无法与 `archive.apache.org` 建立 TCP 连接（IPv4 地址 `65.108.204.189` 连接超时，IPv6 地址 `2a01:4f9:1a:a084::2` 网络不可达），导致 wget 下载 Spark 3.4.2 压缩包失败（exit code: 4）。

### 与 PR 变更的关联

PR 新增了 Kyuubi 1.11.1 on openEuler 24.03-LTS-SP4 的 Dockerfile。其中第 23 行通过 `wget https://archive.apache.org/dist/spark/...` 下载 Spark 二进制包，该 URL 使用的是 Apache 归档站 `archive.apache.org`。与该 PR 代码逻辑无关，属于 CI 构建环境到 `archive.apache.org` 的网络不可达问题。注意：同 Dockerfile 中从 `downloads.apache.org` 下载 Kyuubi 的步骤（第 15 行，step #8）成功，说明网络问题仅限于 `archive.apache.org` 这一特定主机。

**附加发现**：Docker 构建输出中有 1 个 warning：`FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`，即 `FROM ${BASE} as builder` 中 `as` 应为大写 `AS`。此 warning 不影响构建结果，但建议顺手修正以保持风格一致。

## 修复方向

### 方向 1（置信度: 高）
将 Spark 下载源从 `archive.apache.org` 替换为 CI 环境可达的镜像站。历史案例中相同模式（模式33）已验证的方案：
- `dlcdn.apache.org`：优先尝试（PR #3101 对 Knox 2.1.0 使用此方案成功），但需确认 Spark 3.4.2 在 CDN 上是否可用（CDN 通常仅保留最新 1-2 个版本）。
- `repo.huaweicloud.com`：若 CDN 无此版本，则使用华为云镜像站（PR #3077 对 Accumulo 3.0.0 使用此方案成功）。

### 方向 2（置信度: 高）
若 Spark 3.4.2 在 `dlcdn.apache.org` 和 `repo.huaweicloud.com` 均不可用，可考虑从 Spark 官方 GitHub Release 页面（`https://github.com/apache/spark/releases`）下载，需确认该 URL 在 CI 环境中可达。

## 需要进一步确认的点
- 确认 `dlcdn.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz` 是否存在（CDN 可能仅保留最新版本）。
- 确认 `repo.huaweicloud.com/apache/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz` 在 CI 环境中是否可达、是否可用。
- 验证 Spark 3.4.2 制品的 SHA 校验值，确保镜像站下载的文件完整性。

## 修复验证要求
若采用 `dlcdn.apache.org` 方案，需确认 Spark 3.4.2 确实存在于 CDN 路径中；若仅存在 `archive.apache.org`，需改用华为云等镜像站。code-fixer 在提交前必须验证所选镜像站的 Spark 3.4.2 下载 URL 确实可访问且返回正确的压缩包。
