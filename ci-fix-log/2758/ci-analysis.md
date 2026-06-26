# CI 失败分析报告

## 基本信息
- PR: #2758 — 【自动升级】qemu容器镜像升级至11.0.2版本.
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式02
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.076 --2026-06-26 03:40:20--  https://download.qemu.org/qemu-11.0.2.tar.xz
#9 0.121 Resolving download.qemu.org (download.qemu.org)... 156.146.44.90, 95.173.197.105, 84.17.57.27, ...
#9 0.223 Connecting to download.qemu.org (download.qemu.org)|156.146.44.90|:443... connected.
#9 0.283 HTTP request sent, awaiting response... 404 Not Found
#9 0.805 2026-06-26 03:40:21 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://download.qemu.org/qemu-${VERSION}.tar.xz ..." did not complete successfully: exit code: 8
ERROR: failed to solve: process "/bin/sh -c wget https://download.qemu.org/qemu-${VERSION}.tar.xz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Cloud/qemu/11.0.2/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 中 `ARG VERSION=11.0.2` 指定的 QEMU 版本 `11.0.2` 在 `https://download.qemu.org/` 上不存在（HTTP 404），导致 `wget` 下载源码包失败。

### 与 PR 变更的关联
PR 新增了 qemu 11.0.2 的 Dockerfile（`Cloud/qemu/11.0.2/24.03-lts-sp3/Dockerfile`），Dockerfile 中 `ARG VERSION=11.0.2` 以及 `wget https://download.qemu.org/qemu-${VERSION}.tar.xz` 是本次 PR 引入的内容。构建在第 4/6 步（下载源码）失败，依赖安装步骤（第 2/6 步 `dnf install`）已成功完成。失败直接由 PR 新增的 Dockerfile 中指定的版本号 11.0.2 触发——该版本在 QEMU 官方下载服务器上不存在。

## 修复方向

### 方向 1（置信度: 高）
QEMU 上游未发布 11.0.2 版本。需确认 QEMU 官方实际发布的最新版本号，将 Dockerfile 中 `ARG VERSION` 改为上游实际存在的版本。例如检查 `https://download.qemu.org/` 目录确认可用的 11.x 系列最高版本（如 11.0.0 或 11.0.1），或降级到已验证可用的版本。同时同步更新 `README.md`、`doc/image-info.yml`、`meta.yml` 中的版本号。

### 方向 2（置信度: 中）
如果 QEMU 上游已发布 11.0.2 但使用了不同的文件命名或下载路径，需调整 Dockerfile 中的下载 URL 模板以匹配实际的文件路径结构（如版本目录层级或归档文件名格式）。

## 需要进一步确认的点
- 确认 `https://download.qemu.org/` 上当前可用的 QEMU 11.x 系列最高版本号。
- 确认 QEMU 11.0.2 是否已正式发布但托管在其他路径（如预发布目录）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次为下载 URL 404 问题，不涉及正则 patch 操作。）
