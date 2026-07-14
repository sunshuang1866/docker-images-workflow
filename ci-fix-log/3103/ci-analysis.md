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
#9 [builder 4/5] RUN wget https://archive.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz ...
#9 0.108 --2026-07-14 08:01:10--  https://archive.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz
#9 0.176 Resolving archive.apache.org (archive.apache.org)... 65.108.204.189, 2a01:4f9:1a:a084::2
#9 0.534 Connecting to archive.apache.org (archive.apache.org)|65.108.204.189|:443... failed: Connection timed out.
#9 134.9 Connecting to archive.apache.org (archive.apache.org)|2a01:4f9:1a:a084::2|:443... failed: Network is unreachable.
#9 ERROR: process "/bin/sh -c wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && ..." did not complete successfully: exit code: 4
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:23`
- 失败原因: CI 构建环境无法连接 `archive.apache.org`（IPv4 连接超时、IPv6 网络不可达），导致 wget 下载 Spark 3.4.2 失败（exit code: 4）。此前一步（Kyuubi 从 `downloads.apache.org` 下载）成功完成，证明网络故障仅限于 `archive.apache.org` 域名。

### 与 PR 变更的关联
PR 新增了 Kyuubi 1.11.1 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。Dockerfile 中从 `archive.apache.org` 下载 Spark 二进制包，而 CI runner 无法访问该域名。Dockerfile 代码本身正确——这是 CI 基础设施的网络连通性问题，与 PR 代码逻辑无关。历史的同类型 SP4 镜像构建（PR #3077、#3101、#3108）也遭遇了同样的 `archive.apache.org` 连通性问题。

## 修复方向

### 方向 1（置信度: 高）
将 Spark 下载源从 `archive.apache.org` 切换为 CI 构建环境可达的镜像站。参考历史修复案例：
- PR #3077（accumulo）：Zookeeper 下载源从 `archive.apache.org` 换为 `repo.huaweicloud.com`
- PR #3101（knox）：`downloads.apache.org` 换为 `dlcdn.apache.org`

对于 Spark，可将 `archive.apache.org/dist/spark` 替换为 `dlcdn.apache.org/spark` 或华为云镜像站的对应路径。

### 方向 2（置信度: 中）
同时修正 Dockerfile 中的 lint 警告：第 3 行 `FROM ${BASE} as builder` 中的 `as` 应改为大写 `AS`（与 Dockerfile 最佳实践一致），但该警告不导致构建失败。

## 需要进一步确认的点
- 需确认 `dlcdn.apache.org` 或 `repo.huaweicloud.com` 上是否存在 `spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz` 的对应路径及文件
- 若更换下载源后仍失败，需排查 CI runner 对替代域名的连通性

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用（本次修复不涉及正则 patch 外部源文件）。
