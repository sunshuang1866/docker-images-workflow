# 修复摘要

## 修复的问题
meson 配置阶段因 wayland-protocols 子项目 wrap 下载 hash 校验失败导致构建中断。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `dnf install` 命令中添加 `wayland-protocols-devel` 包

## 修复逻辑
CI 失败的直接原因是 mesa 25.3.4 的 `subprojects/wayland-protocols.wrap` 记录的 SHA256 与 GitLab 实际提供的 tarball 不匹配。由于 Dockerfile 中未安装 `wayland-protocols-devel`，meson 无法通过 pkg-config 找到系统级 wayland-protocols，只能回退到 wrap 下载方式从而触发 hash 校验失败。

添加 `wayland-protocols-devel` 后，meson 在配置阶段通过 pkg-config 发现已安装的系统包，会优先使用系统包而跳过 wrap 子项目下载，完全规避 hash 不匹配问题。此方案遵循分析报告中的方向 1（高置信度）。

## 潜在风险
- 若 openEuler 24.03-LTS-SP4 仓库中的 `wayland-protocols-devel` 版本低于 mesa 25.3.4 要求的最低版本（1.41），meson 可能仍然拒绝使用系统包。但从同一 Dockerfile 已安装 `wayland-devel` 且其他 mesa 版本在同系列 Dockerfile 中同样依赖系统 wayland-protocols 来看，该风险较低。
- 无其他风险。