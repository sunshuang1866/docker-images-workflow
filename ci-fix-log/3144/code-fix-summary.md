# 修复摘要

## 修复的问题
builder 阶段基于 `lukemathwalker/cargo-chef:latest-rust-1.85-bookworm`（Debian Bookworm）镜像，其 CA 证书信任链不包含 Intel CDN（`apt.repos.intel.com`，由 Akamai 提供服务）的 TLS 证书颁发机构，导致 `wget` 下载 Intel GPG 公钥和 `apt-get` 访问 Intel 仓库时证书验证失败。

## 修改的文件
- `AI/text-embeddings-inference-cpu/1.7.0/24.03-lts-sp4/Dockerfile`: 在 builder 阶段的 `wget` 和 `apt-get` 访问 Intel 仓库之前，添加 `RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates` 步骤（第 38 行），确保 CA 证书信任库是最新的。

## 修复逻辑
分析报告根因定位：builder 阶段的基础镜像（cargo-chef/Bookworm）缺少对 Intel CDN 证书的信任。Debian 官方仓库的 HTTPS 访问正常，说明问题仅限于 Intel CDN 的证书链。

修复方案采用分析报告中的"方向 1"：在访问 Intel 仓库之前先安装/更新 `ca-certificates` 包并刷新证书信任库。新增的 `RUN` 步骤：
1. `apt-get update` — 从 Debian 官方仓库（已验证可正常访问）更新软件包索引
2. `apt-get install -y ca-certificates` — 安装/更新 CA 证书包
3. `update-ca-certificates` — 刷新 `/etc/ssl/certs/` 中的证书哈希链接

此修复仅增加一个独立的 `RUN` 层，不影响后续的 `wget`、`gpg`、`apt-get` 等步骤的逻辑。

## 潜在风险
- 新增的 `RUN` 层会增加镜像构建层数（+1 层），但对最终镜像大小无影响（builder 为中间阶段，不会被最终镜像继承）。
- 如果 Debian 官方仓库的 `ca-certificates` 包版本仍不包含 Intel CDN 的新证书，此修复可能无效。此时需要回退到使用 `[trusted=yes]` 或 `--no-check-certificate` 作为后备方案。