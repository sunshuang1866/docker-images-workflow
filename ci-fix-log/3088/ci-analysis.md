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
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，只托管当前最新版本，Druid 35.0.0 已从 CDN 下架，导致 `wget` 请求返回 HTTP 404

### 与 PR 变更的关联
PR 新增的 Dockerfile `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 第 9 行 `RUN wget` 使用 `dlcdn.apache.org/druid/${VERSION}/` 作为下载源。该 URL 在 Druid 35.0.0 仍为最新版时有效，但当前 CDN 上已不再保留该版本（已被更新版本替换），导致构建失败。此问题与 PR 的代码变更有直接关联，但与代码逻辑错误无关，属于上游版本生命周期问题。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`。Apache Archive 仓库（`https://archive.apache.org/dist/druid/`）会永久保留所有历史版本的二进制制品。修改 Dockerfile 第 9 行的 wget URL，将 `https://dlcdn.apache.org/druid/${VERSION}/` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/`，并确认归档路径格式（通常 Archive 的路径层级与 CDN 一致）。

### 方向 2（置信度: 中）
将 Druid 版本从 35.0.0 升级到当前 `dlcdn.apache.org` 仍托管的更高版本（需先确认 CDN 上当前可用版本）。但这会与 PR 目录名 `35.0.0` 和 `meta.yml` 中定义的版本号不一致，需同步更新目录结构和所有元数据文件。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可被 CI 构建环境访问
- 确认 `archive.apache.org` 的连接稳定性（参考模式33，部分 Apache 域名在 CI 环境中可能不可达；若不可达，可考虑华为云镜像站 `repo.huaweicloud.com` 作为备选源）

## 修复验证要求
code-fixer 在提交前，必须使用 `wget --spider` 或 `curl -I` 验证替换后的下载 URL 返回 HTTP 200（而非 404 或连接超时）。若 `archive.apache.org` 不可达，需进一步尝试 `repo.huaweicloud.com/apache/druid/` 等镜像站。
