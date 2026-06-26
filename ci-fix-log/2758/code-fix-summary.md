# 修复摘要

## 修复的问题
QEMU 11.0.2 版本在上游下载服务器不存在（HTTP 404），将版本号修正为实际存在的 11.0.1。

## 修改的文件
- `Cloud/qemu/11.0.2/24.03-lts-sp3/Dockerfile`: `ARG VERSION=11.0.2` → `ARG VERSION=11.0.1`
- `Cloud/qemu/meta.yml`: 标签 `11.0.2-oe2403sp3` → `11.0.1-oe2403sp3`
- `Cloud/qemu/README.md`: 版本引用 `11.0.2` → `11.0.1`
- `Cloud/qemu/doc/image-info.yml`: 版本引用 `11.0.2` → `11.0.1`

## 修复逻辑
从 `https://download.qemu.org/` 目录列表确认，QEMU 11.x 系列当前最高稳定版本为 11.0.1（文件 `qemu-11.0.1.tar.xz` 存在）。11.0.2 尚未发布，导致 `wget https://download.qemu.org/qemu-11.0.2.tar.xz` 返回 404。将 Dockerfile 及所有关联文件中的版本号从 11.0.2 改为 11.0.1，使下载 URL 指向实际存在的文件。

## 潜在风险
- Dockerfile 所在目录仍保持原名 `11.0.2/`（因约束不允许创建/重命名目录），仅文件内容中的版本号已修正为 11.0.1。实际构建产物为 qemu 11.0.1，目录名与内容版本存在不一致，但不影响构建和运行。