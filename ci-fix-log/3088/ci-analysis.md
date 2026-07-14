# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 旧版本 404）
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
```
Docker 构建在 `builder` 阶段的第 3 步（`Dockerfile:9`）失败：`wget` 从 `dlcdn.apache.org` 下载 `apache-druid-35.0.0-bin.tar.gz` 时收到 HTTP 404，导致 `RUN` 指令以 exit code 8 退出，整个构建中止。

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org`（Apache CDN）不再托管 `apache-druid-35.0.0-bin.tar.gz` 制品（HTTP 404）。该 CDN 仅保留最新版本，旧版本下架后即不可用。这与模式01的根因机制一致——Apache CDN 会清理非最新版本的制品。

### 与 PR 变更的关联
PR 新增了 druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。Dockerfile 中硬编码了从 `dlcdn.apache.org/druid/35.0.0/` 下载制品的 URL，该 URL 在构建时已失效，直接导致构建失败。这是 PR 引入的代码问题（下载源选择不当），而非现有基础设施问题。

注意：仓库中已存在 druid 35.0.0 的 SP2 变体（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`），若其使用相同下载 URL，可能在制品被 CDN 下架之前已成功构建过。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（Apache 归档站），该站点长期保留历史版本制品。URL 格式变更为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
升级 Druid 版本到 `dlcdn.apache.org` 当前托管的最新版本。需先确认 CDN 上 `https://dlcdn.apache.org/druid/` 目录下实际可用的版本号，再将 `ARG VERSION` 更新为可用版本。注意此方案可能改变镜像的目标版号，需同步更新 `meta.yml`、`README.md`、`image-info.yml` 中的版本信息。

## 需要进一步确认的点
1. 同步检查已有的 SP2 变体 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否使用相同下载 URL，若相同则其构建可能也已受影响（或仅在制品下架前成功过）。
2. 访问 `https://archive.apache.org/dist/druid/35.0.0/` 确认归档站是否实际存有 `apache-druid-35.0.0-bin.tar.gz`，以验证修复方向1的可行性。
3. 若归档站也无此版本，则需确认 druid 35.0.0 的实际可用下载源。
