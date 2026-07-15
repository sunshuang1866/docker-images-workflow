# 修复摘要

## 修复的问题
bzip2/1.0.8 源码下载 403 Forbidden 导致 conan install 失败，进而 `make build-cpp` 中断。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 将 `bzip2_source_fix.py` hook 中的替换目标 URL 和预下载 URL 从 `distfiles.macports.org` 替换为 `mirrors.kernel.org`

## 修复逻辑
CI 环境中 `distfiles.macports.org/bzip2/bzip2-1.0.8.tar.gz` 返回 403 Forbidden，导致 conan hook 替换后的 URL 同样不可达，`source()` 方法下载失败。`mirrors.kernel.org` 是 Linux 基金会运营的可靠镜像，已在本环境验证返回 200 且文件正确（810029 字节 gzip 压缩包）。替换该 URL 可绕过 macports 的 IP 封禁问题。

## 潜在风险
如果 CI 环境同样封锁 `mirrors.kernel.org`，则此问题属于 infra-error，需要排查 CI 网络出口配置。当前环境下 `mirrors.kernel.org` 验证可正常访问。