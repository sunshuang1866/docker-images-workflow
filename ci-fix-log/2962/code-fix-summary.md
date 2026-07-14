# 修复摘要

## 修复的问题
openEuler 24.03-LTS-SP4 系统仓库中 wayland-protocols-devel 仅提供 1.33 版本，不满足 mesa 25.3.4 对 wayland-protocols >= 1.41 的要求，导致 meson 回退到下载 fallback 子项目时因 SHA256 哈希不匹配而构建失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `meson setup build`（mesa）之前新增一步，从 GitLab 下载 wayland-protocols 1.41 源码并使用 meson 构建安装到 `/usr/local`，使 mesa 的 meson 能通过 pkg-config 检测到 >= 1.41 的系统依赖，不再触发 fallback 子项目下载。

## 修复逻辑
在 pip 安装 meson/ninja 之后、mesa 的 meson setup 之前，新增 RUN 步骤：
1. 从 GitLab releases 下载 wayland-protocols-1.41.tar.xz
2. 解压并用 meson 构建安装（默认安装到 `/usr/local`）
3. 清理临时文件

这样 mesa 的 meson setup 会通过 pkg-config 在 `/usr/local` 中找到 wayland-protocols 1.41，满足 >= 1.41 的版本要求，不再触发 subprojects/wayland-protocols.wrap 的 fallback 下载和哈希校验。此修复遵循分析报告中的"方向 1（置信度: 高）"。

## 潜在风险
- GitLab 自动生成的 tarball（`/-/releases/.../downloads/` 路径）的哈希值不具确定性，但在本修复中仅用于下载和构建（不涉及哈希校验），无风险。
- wayland-protocols 1.41 从源码构建仅需 meson 和 ninja（已在 pip 步骤中安装），无需额外系统依赖，无新增依赖风险。
- 安装到 `/usr/local` 不会覆盖系统 dnf 安装的 wayland-protocols 1.33 文件（位于 `/usr`），两者共存，由 pkg-config 路径优先级决定使用 1.41。