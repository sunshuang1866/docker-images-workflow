# CI 失败分析报告

## 基本信息
- PR: #2659 — 【自动升级】redis容器镜像升级至5.4.1版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式02
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.923 --2026-06-19 01:14:12--  https://github.com/redis/redis/archive/refs/tags/5.4.1.tar.gz
#9 1.466 Location: https://codeload.github.com/redis/redis/tar.gz/refs/tags/5.4.1 [following]
#9 1.605 HTTP request sent, awaiting response... 404 Not Found
#9 1.888 2026-06-19 01:14:13 ERROR 404: Not Found.
#9 1.892 gzip: stdin: unexpected end of file
#9 1.892 tar: Child returned status 1
#9 1.892 tar: Error is not recoverable: exiting now
```

### 根因定位
- 失败位置: `Database/redis/5.4.1/24.03-lts-sp3/Dockerfile`:13 (RUN 指令中的 wget 行)
- 失败原因: 版本 `5.4.1` 不是合法的 Redis 发布版本——Redis 官方 GitHub 仓库 (`github.com/redis/redis`) 中不存在 `5.4.1` 标签。Redis 5.x 系列的实际版本为 5.0.x（如 5.0.14），`5.4.1` 这个版本号从未存在过，因此 `wget https://github.com/redis/redis/archive/refs/tags/5.4.1.tar.gz` 返回 HTTP 404。

### 与 PR 变更的关联
本次 PR 完全由自动升级系统生成，所有文件均为新增（`new_file: True`），包括：
- `Database/redis/5.4.1/24.03-lts-sp3/Dockerfile` — 其中 `ARG VERSION=5.4.1` 直接使用了这个不存在的版本号
- `Database/redis/5.4.1/24.03-lts-sp3/entrypoint.sh` — 配套启动脚本
- 元数据文件（`meta.yml`, `image-info.yml`, `README.md`）中的版本条目

失败由 PR 引入的 Dockerfile 中 `VERSION=5.4.1` 直接触发。版本号不合法，导致源码下载 404，后续所有操作（tar 解压、grep/sed 修改 config.c、jemalloc 配置、make 编译）全部级联失败。

## 修复方向

### 方向 1（置信度: 高）
确认 Redis 5.x 系列的最新可用版本（应为 5.0.x，如 `5.0.14`），将 `ARG VERSION` 修正为实际存在且可下载的版本号，同时更新目录名、meta.yml 和 image-info.yml 中的版本引用。若期望的不是 Redis 5.0.x 而是其他大版本，应确认上游实际最新版本号后修正。

### 方向 2（置信度: 中）
如果自动升级系统生成了错误的版本号 `5.4.1`，可能上游存在对应的 Redis fork 或不同命名规则的发布源。需要验证：是否存在使用 `5.4.1` 版本号的 Redis 兼容发行版（如其他仓库的 Redis fork），若有则更换下载 URL 源地址；若没有，则按方向 1 修正版本号。

## 需要进一步确认的点
1. 自动升级系统从何处获取了版本号 `5.4.1`？需要追溯升级系统的版本源数据，确认版本号生成逻辑是否存在 bug 或将其他包管理器的 redis 版本号（如 RPM 包的 epoch:version-release）误解析为上游源码版本。
2. Redis 社区当前实际可用的稳定版本是什么？若意图升级 5.x 系列，最新为 5.0.14；若意图跟随最新稳定版，当前为 8.2.x 系列。
3. 本次升级的意图：是跟随特定大版本（5.x/6.x/7.x/8.x）的最新小版本，还是升级到绝对最新的稳定版？

## 修复验证要求
若按方向 1 修正版本号，code-fixer 必须在提交前验证：
- 在浏览器或 `wget --spider` 中确认新版本号的 GitHub archive URL 返回 200（而非 404）
- 确认新版本目录下的 Dockerfile 中 `VERSION` 变量与目录名一致
- 同步更新 `meta.yml`、`doc/image-info.yml`、`README.md` 中所有版本引用
