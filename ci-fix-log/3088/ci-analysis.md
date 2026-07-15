# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（同类根因，不同项目）+ 模式02（症状吻合）
- 新模式标题: -
- 新模式症状关键词: -

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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget ...` 行）
- 失败原因: `dlcdn.apache.org`（Apache CDN）不再托管 Druid 35.0.0 的二进制包，wget 请求返回 HTTP 404。这与模式01中 Maven 历史版本从 CDN 下架为同一类根因——Apache CDN 仅保留最新版本，旧版本会被移除。

### 与 PR 变更的关联
**直接关联。** PR 新增的 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 第 9 行 `RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 是本次构建失败的直接触发点。该 URL 在 PR 提交时可能仍有效，但到 CI 构建时已被 CDN 移除（与模式01 的历史案例完全一致）。

注意：构建日志中另有一个 Docker 警告 `FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`（`FROM ${BASE} as builder` 中 `as` 为小写），但此警告不是构建失败的原因，且不影响最终结果。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`，后者保留所有历史版本（包括旧版本和已归档版本）。URL 模式为：

- 原: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 改: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

这是 Apache 官方归档服务器，长期保留所有已发布版本的制品，不会被 CDN 轮转清理影响。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在网络环境中不可达（参考模式33的历史经验），可换用 `repo.huaweicloud.com` 华为云镜像站：

- `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

需验证该镜像站是否已同步 Druid 35.0.0 版本。

## 需要进一步确认的点
1. 是否已将 `archive.apache.org` 加入到 CI 构建环境的网络白名单中（参考模式33 中 `downloads.apache.org` / `archive.apache.org` 可能无法可达的历史案例）
2. 同仓库内其他使用 `dlcdn.apache.org` 下载 Druid 的 Dockerfile（如 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否需要同步修复——如果它们也使用了 CDN URL，后续重建时可能遇到同样的 404

## 修复验证要求
code-fixer 在提交前，必须验证 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实可访问且返回 200（可用 `curl -sI` 或 `wget --spider` 确认）。若 `archive.apache.org` 不可达，则验证华为云镜像站或其他备选镜像的可用性后再提交。
