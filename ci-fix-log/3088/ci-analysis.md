# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式02
- 新模式标题: (不适用，已有匹配模式)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz     && tar -zxvf apache-druid-35.0.0-bin.tar.gz     && mv apache-druid-35.0.0 /opt/druid     && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Dockerfile 中 `wget` 从 `dlcdn.apache.org/druid/35.0.0/` 下载 `apache-druid-35.0.0-bin.tar.gz` 时返回 HTTP 404 Not Found，该路径下不存在对应版本的制品文件。

### 与 PR 变更的关联
PR 新增的 Dockerfile 直接使用了 `dlcdn.apache.org` 作为下载源，但该 CDN 的 `/druid/35.0.0/` 路径下没有 `apache-druid-35.0.0-bin.tar.gz` 文件。这与 PR 改动直接相关——下载 URL 构造正确但上游 CDN 未托管此版本制品。

## 修复方向

### 方向 1（置信度: 中）
将下载源从 `dlcdn.apache.org` 切换为 Apache 归档站 `archive.apache.org/dist/druid/35.0.0/`。Apache 归档站通常保留所有历史发行版制品，更适合 CI 构建场景。

### 方向 2（置信度: 低）
检查 `dlcdn.apache.org/druid/` 目录下实际存在的版本列表，确认 `35.0.0` 是否使用不同的文件名格式（如 `apache-druid-35.0.0-src.tar.gz` 而非 `-bin.tar.gz`），或是否仅托管在 `downloads.apache.org` 下。

## 需要进一步确认的点
1. 确认 `apache-druid-35.0.0-bin.tar.gz` 在 Apache 官方下载渠道（`archive.apache.org`、`downloads.apache.org`）的实际存放路径和文件名格式。
2. 对照现有 SP2 版本的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`），确认其下载 URL 是否也使用 `dlcdn.apache.org` 且当时构建成功——若 SP2 的 URL 也不同，说明 druid 的 CDN 路径存在版本间差异。
3. 验证 `https://dlcdn.apache.org/druid/` 根路径下是否确实存在 `35.0.0/` 子目录。

## 修复验证要求
code-fixer 在修改下载 URL 前，必须手动验证目标 URL（如 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）可正常下载（HTTP 200），确认后再提交。
