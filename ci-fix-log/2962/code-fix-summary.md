# 修复摘要

## 修复的问题
Docker 构建时 `wget` 从 `gitlab.freedesktop.org` 下载 wayland-protocols-1.41.tar.xz 失败：服务器返回 HTML 页面（Anubis 反爬保护）而非实际的压缩包，导致 `tar -xvf` 报 `File format not recognized` 错误。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 移除了手动下载 wayland-protocols-1.41 源码并构建的 RUN 步骤（原第 26-31 行）

## 修复逻辑
1. `gitlab.freedesktop.org` 已全面启用 Anubis Proof-of-Work 反爬保护，所有自动化请求（`wget`/`curl`）均会被拦截并返回 HTML 页面，无法直接下载 release assets。
2. DNS 已安装 `wayland-protocols-devel` 包（Dockerfile 第 9 行），该系统包提供了 meson 构建所需的 wayland protocol XML 文件。
3. SP3 版本的 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile`）对同一 mesa 25.3.4 版本的构建不含手动 wayland-protocols 下载步骤，且已验证可成功构建。因此 SP4 版本的手动下载步骤是不必要的冗余操作。
4. 移除冗余的手动下载步骤后，meson 构建将直接使用系统 dnf 安装的 `wayland-protocols-devel` 包中的协议文件。

## 潜在风险
无。SP3 版本已证明同一 mesa 版本在无手动 wayland-protocols 下载的情况下可成功构建；SP4 版本额外安装了 `wayland-protocols-devel` 系统包，协议文件供应更为充足。