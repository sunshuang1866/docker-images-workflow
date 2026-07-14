# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 已下架 Apache Druid 35.0.0 的二进制包（404 Not Found），与模式01机制一致——Apache CDN 仅托管最新版本，旧版本下架后即不可用。

### 与 PR 变更的关联
本次 PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。Dockerfile 中硬编码使用 `dlcdn.apache.org/druid/${VERSION}/` 作为下载源（`Dockerfile:9`）。该 URL 在 Druid 35.0.0 仍为 CDN 当前版本时有效（现有 SP2 的 Dockerfile 在提交时可用），但当前 CDN 上 35.0.0 已被下架，导致新 SP4 Dockerfile 构建时下载失败。失败直接由 PR 新增的 Dockerfile 触发。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/druid/`。Apache 官方归档站 `archive.apache.org` 保留所有历史版本的二进制包，不受 CDN 仅保留最新版的限制。需要确认目标 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可访问。

### 方向 2（置信度: 中）
若 `archive.apache.org` 不可用（参考模式33，`archive.apache.org` 在 CI 环境中存在网络不通的历史案例），可将下载源更换为华为云镜像站等国内镜像，例如 `repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`，但需确认该镜像仓中是否包含 Druid 制品。

## 需要进一步确认的点
- `archive.apache.org/dist/druid/35.0.0/` 路径下是否确实存在 `apache-druid-35.0.0-bin.tar.gz` 文件
- CI 构建环境是否能正常访问 `archive.apache.org`（历史上出现过网络不通的情况，见模式33）
- 同镜像已有 SP2 版本的 Dockerfile 是否也使用了相同的问题 URL 模式，若 SP2 后续触发 rebuild 是否需要同步修复

## 修复验证要求
code-fixer 在提交前，需手动验证目标下载 URL（如 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）确实返回 HTTP 200 且文件可正常下载。若 archive 站不可达，需验证候选镜像站（如华为云镜像站）上对应路径是否存在该 Druid 版本制品。
