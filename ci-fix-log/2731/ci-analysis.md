# CI 失败分析报告

## 基本信息
- PR: #2731 — 【自动升级】mongoose容器镜像升级至7.22版本
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式02
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 0.081 --2026-06-24 01:29:40--  https://github.com/cesanta/mongoose/archive/refs/tags/7.22.tar.gz
#12 0.297 HTTP request sent, awaiting response... 302 Found
#12 0.337 Location: https://codeload.github.com/cesanta/mongoose/tar.gz/refs/tags/7.22 [following]
#12 0.482 HTTP request sent, awaiting response... 404 Not Found
#12 0.734 2026-06-24 01:29:41 ERROR 404: Not Found.
#12 ERROR: process "/bin/sh -c wget https://github.com/cesanta/mongoose/archive/refs/tags/${VERSION}.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Others/mongoose/7.22/24.03-lts-sp3/Dockerfile:12`（`RUN wget ...` 步骤）
- 失败原因: Dockerfile 中 `ARG VERSION=7.22` 构造的下载 URL `https://github.com/cesanta/mongoose/archive/refs/tags/7.22.tar.gz` 在 GitHub 返回 404——上游仓库 `cesanta/mongoose` 中不存在名为 `7.22` 的 Git tag。

### 与 PR 变更的关联
PR 新增了 mongoose 7.22 的 Dockerfile（`Others/mongoose/7.22/24.03-lts-sp3/Dockerfile`），其中 `ARG VERSION=7.22` 和下载 URL 是首次引入。该 Dockerfile 直接触发了本次失败。失败与 PR 无关的其他改动（README.md、image-info.yml、meta.yml）无直接关联。

## 修复方向

### 方向 1（置信度: 中）
上游仓库 `cesanta/mongoose` 的 Git tag 可能使用带 `v` 前缀的格式（如 `v7.22`）而非裸版本号。可将 Dockerfile 中的 `VERSION` 从 `7.22` 改为 `v7.22`（同时保持目录名 `7.22` 不变），或修改 `wget` 的 URL 中 tag 引用方式（如 `${VERSION#v}` 配合 `VERSION=v7.22`）。

### 方向 2（置信度: 中）
mongoose 7.22 版本可能尚未在 GitHub 发布（上游尚未推送对应 tag），或其他现有版本（如 7.21）才是最新版。需确认 `https://github.com/cesanta/mongoose/tags` 中是否确实存在 7.22 相关 tag。若不存在，此自动升级 PR 应关闭或等待上游正式发布。

### 方向 3（置信度: 低）
tag 格式可能为其他变体（如 `7.22.0`）。需查看上游仓库确认实际 tag 命名规则后修正。

## 需要进一步确认的点
1. 访问 `https://github.com/cesanta/mongoose/tags` 确认 tag `7.22`、`v7.22`、`7.22.0` 中哪一个（或都不）实际存在
2. 对比同仓库 mongoose 7.21 版本 Dockerfile 中的 `VERSION` 值和 tag 引用方式，确认历史版本的 tag 命名模式
3. 确认 mongoose 7.22 是否已经正式发布（自动升级流程可能过早触发）

## 修复验证要求
code-fixer 在提交修复前，必须手动或通过 `git ls-remote --tags https://github.com/cesanta/mongoose.git` 确认正确的 tag 名称，并通过 `wget` 实际测试下载 URL 可访问后再提交。
