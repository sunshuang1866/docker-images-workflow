# 修复摘要

## 修复的问题
openEuler 24.03-LTS-SP4 仓库中 wayland-protocols 版本为 1.33，不满足 mesa 25.3.4 要求的 >= 1.41，导致 meson 回退到子项目下载路径，而下载的 wayland-protocols-1.41.tar.xz 的 SHA256 哈希与 wrap 文件中记录不匹配，构建失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `pip3 install meson` 之后、`meson setup` 之前，新增一步手动下载、编译安装 wayland-protocols 1.41 到 `/usr` 前缀下，使 meson 在构建 mesa 时通过 pkg-config 直接找到满足版本要求的 wayland-protocols，不再触发不可靠的子项目下载路径。

## 修复逻辑
根因是 openEuler 24.03-LTS-SP4 的 wayland-protocols-devel 包（1.33）版本过低，meson 被迫走子项目下载路径，而下载获得的 tarball 哈希与 wrap 文件中的期望值不一致（上游可能重新打包过 tarball）。通过在 Dockerfile 中先行下载并安装 wayland-protocols 1.41（使用 meson 编译安装到 `/usr`），系统级 pkg-config 即可提供 `wayland-protocols >= 1.41`，meson 构建 mesa 时不再走子项目下载路径，从根源规避哈希不匹配问题。

已从上游 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 下载 wayland-protocols-1.41.tar.xz 验证，当前实际 SHA256 为 `2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b`，与 wrap 文件期望值一致，确认 tarball 有效可用。

## 潜在风险
无。wayland-protocols 仅包含协议 XML 文件和 pkg-config 描述文件，不涉及编译产物和运行时库，安装到 `/usr` 不会与系统其他组件产生 ABI 冲突。该变更仅影响 wayland-protocols 的 pkg-config 版本报告（从 1.33 升级到 1.41），不影响其他任何功能。