# CI 失败分析报告

## 基本信息
- PR: #3103 — chore(kyuubi): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33, 模式09
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.108 --2026-07-14 08:01:10--  https://archive.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz
#9 0.176 Resolving archive.apache.org (archive.apache.org)... 65.108.204.189, 2a01:4f9:1a:a084::2
#9 0.534 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#9 134.9 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#9 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz &&     mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark &&     rm -f spark-${SPARK_VERSION}-bin-hadoop3.tgz" did not complete successfully: exit code: 4
------
Dockerfile:23
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:23`（wget 下载 Spark 步骤）
- 失败原因: CI 构建环境无法与 `archive.apache.org` 建立 TCP 连接（IPv4 地址 `65.108.204.189:443` Connection timed out，IPv6 地址 `2a01:4f9:1a:a084::2:443` Network is unreachable），导致 wget 下载 Spark 3.4.2 二进制包超时失败（exit code: 4）。同时，`downloads.apache.org`（Kyuubi 下载步骤 #8）可达并成功完成。

### 与 PR 变更的关联
PR #3103 新增了 `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`，其中第 23 行使用 `archive.apache.org` 下载 Spark 3.4.2。该 URL 在 CI 构建环境中不可达，属于基础设施网络问题，与代码逻辑正确性无关。但 Dockerfile 中同时存在 **模式09（BUILDARCH 冲突）** 的潜在缺陷——`RUN` 中对 `BUILDARCH` 变量重新赋值与 BuildKit 预定义全局 ARG 冲突，该问题在 Spark 下载步骤之后会被触发。

## 修复方向

### 方向 1（置信度: 高）
**将 Spark 下载源从 `archive.apache.org` 切换为 `repo.huaweicloud.com` 镜像站**（同模式33历史案例 PR #3077、#3108 的处理方式）。将下载 URL 从：
`https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz`
改为：
`https://repo.huaweicloud.com/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz`

### 方向 2（置信度: 高）
**修复 BUILDARCH 变量冲突（模式09）**。Dockerfile 中 `BUILDARCH` 是 BuildKit 预定义全局 ARG，在 `RUN` 中重新赋值会被覆盖回内置值。将变量名从 `BUILDARCH` 改为自定义名称（如 `JAVA_ARCH`），与 PR #2105（同为 kyuubi 仓库）的修复方式一致。

```dockerfile
# 变更前（存在冲突）
RUN if [ "$TARGETARCH" = "amd64" ]; then \
      BUILDARCH="x64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      BUILDARCH="aarch64"; \
    fi ...wget .../jre/${BUILDARCH}/...

# 变更后使用自定义变量名 JAVA_ARCH
```

## 需要进一步确认的点
- 确认 `repo.huaweicloud.com/apache/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz` 在华为云镜像站确实存在且可访问
- 确认修复方向 1 和方向 2 同时应用后，Docker 构建能通过全部步骤

## 修复验证要求
1. code-fixer 提交前需验证 `repo.huaweicloud.com/apache/spark/spark-3.4.2/` 目录下 `spark-3.4.2-bin-hadoop3.tgz` 文件存在且可下载
2. code-fixer 提交前需验证 `BUILDARCH` 重命名后，JDK JRE URL 构造正确（清华镜像站路径结构覆盖 x64 和 aarch64 两种架构）
