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
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
------
Dockerfile:9
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`wget` 下载 Druid 压缩包步骤）
- 失败原因: `dlcdn.apache.org`（Apache CDN）对 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，该 CDN 通常只保留最新版本释放的制品，旧版本（如 Druid 35.0.0）可能已被下架。

### 与 PR 变更的关联
PR 新增了一个完整的 Dockerfile 用于在 openEuler 24.03-LTS-SP4 上构建 Druid 35.0.0 镜像。构建过程中 `builder` 阶段的 `wget` 步骤直接从 `dlcdn.apache.org` 下载 Druid 二进制包时遭遇 404，导致整个镜像构建失败。错误直接由新增 Dockerfile 中的下载 URL 触发，属于 PR 新增代码引入的问题。已有 SP2 版本的 Dockerfile 可能同样使用此 URL 但当时制品可用；随着时间推移，CDN 已清除该版本，新构建时即失败。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/`（Apache 官方归档站，保留所有历史版本），URL 模板改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 环境中不可达（参考历史模式33），可切换至华为云镜像站或其他已验证可达的 Apache 镜像站。

## 需要进一步确认的点
1. 确认 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在 `apache-druid-35.0.0-bin.tar.gz` 文件。
2. 确认同一版本 35.0.0 的 24.03-lts-sp2 Dockerfile 当前是否也因相同 URL 失败——如果是，应一并修复。
3. 确认 CI 构建环境可正常访问 `archive.apache.org`（参考模式33 中曾出现过 `archive.apache.org` 不可达的情况）。

## 修复验证要求
- code-fixer 必须在修改前，通过 `wget --spider` 或 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，确认替换后的 URL 可正常下载。
- 若 `archive.apache.org` 不可达，需在 CI 环境中测试候选镜像站（如华为云镜像站）的可用性后再提交。
