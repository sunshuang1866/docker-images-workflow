# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38（同根因）
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
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org`（Apache CDN 分发节点）已下架 Druid 35.0.0 的二进制包，wget 请求返回 HTTP 404。这与模式01（Maven CDN 404）和模式38（ActiveMQ CDN 404）的根因完全一致——`dlcdn.apache.org` 仅托管当前最新版本，历史版本被清理后即返回 404。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其 Dockerfile 第 9 行使用 `dlcdn.apache.org` 作为 Druid 35.0.0 的下载源。当 Apache CDN 已下架该版本时，构建必然失败。这是本次 PR 改动直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 替换为 Apache 归档站或其他可用镜像站。参考历史案例中已验证可行的替代源：
- `archive.apache.org/dist/druid/` — Apache 官方归档站，长期保留历史版本
- `repo.huaweicloud.com/apache/druid/` — 华为云镜像站，已验证对 CI 环境兼容性好（模式01、模式33 历史案例）

具体为将 Dockerfile 第 9 行的 URL 从：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
更换为归档站或镜像站的对应路径。

### 方向 2（置信度: 中）
升级 Druid 版本到 `dlcdn.apache.org` 当前可用的最新版本（如 CDN 上仍保留了某个更新版本）。此方向适用于对版本无严格要求的场景，但当前 PR 明确要求 Druid 35.0.0，且上游可能已无更新的 35.x 线版本。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/` 或 `repo.huaweicloud.com/apache/druid/35.0.0/` 中是否存在 `apache-druid-35.0.0-bin.tar.gz`（文件名和路径结构在不同镜像站间可能不同）
- 确认该仓库中已有的 Druid SP2 版本（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）使用的是什么下载源，作为参考保持一致

## 修复验证要求
无需额外验证。下载源更换后，code-fixer 应确保 wget 能成功下载并完成 Docker 构建（即 RUN 命令中所有步骤均通过），即可提交。
