# 修复摘要

## 修复的问题
移除了 Dockerfile 中错误的 `sed` 命令，该命令将 `subprojects/wayland-protocols.wrap` 中的 `source_hash` 覆盖为错误值 `5a2712e6...`，导致 meson 子项目哈希校验失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 删除第 23 行 `RUN sed -i 's/source_hash = .*/source_hash = 5a2712e6...'`，该命令会将正确的哈希值覆盖为错误值。

## 修复逻辑
CI 分析报告指出 `meson setup` 阶段 wayland-protocols 子项目哈希不匹配，错误日志显示 `5a2712e6... expected`、`0b6d27... actual`。检查后发现：

1. Mesa 25.3.4 源码 tarball 中的 `subprojects/wayland-protocols.wrap` 已包含哈希值 `2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b`
2. PR 作者添加的 `sed` 命令将哈希强行覆盖为 `5a2712e6...`（错误的期望值）
3. 从上游 GitLab `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 已重新下载文件并计算 SHA256，确认当前实际哈希为 `2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b`，与 wrap 文件中的原始哈希完全一致

因此，移除错误的 `sed` 命令即可让 meson 使用 wrap 文件中的正确哈希值，校验通过。

## 潜在风险
如果 GitLab 上的 wayland-protocols 1.41 发行包未来再次被重新生成导致哈希变化，则构建可能再次失败。当前已验证上游 hash 与实际下载 hash 匹配，短期内风险较低。