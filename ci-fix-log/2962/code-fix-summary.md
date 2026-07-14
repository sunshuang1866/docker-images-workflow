# 修复摘要

## 修复的问题
删除了 Dockerfile 中两行错误的 `sed` 命令——它们将 wayland-protocols wrap 文件的 `source_url` 和 `source_hash` 覆盖为错误值，导致 meson 配置阶段下载 wayland-protocols 1.41 时返回 HTTP 404。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 移除第 26-27 行的两行 `sed` 命令（原 `RUN sed -i ... subprojects/wayland-protocols.wrap` 的行），保留其余构建步骤不变。

## 修复逻辑
1. mesa 25.3.4 源码中自带的 `subprojects/wayland-protocols.wrap` 上游文件已包含正确的值：
   - `source_url = https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz`
   - `source_hash = 2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b`
2. 原 Dockerfile 中的 `sed` 命令将 `source_url` 错误地覆盖为 `https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz`（该 URL 返回 404），`source_hash` 也覆盖为不匹配的值（`cea75b0a...`）。
3. 同一 mesa 版本的 sp3 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile`）没有这些 sed patch，构建正常。
4. 修复方案：直接删除两行 sed 命令，让 meson 使用上游 wrap 文件中的正确值进行子项目下载。已从上游 `mesa-25.3.4` tag 获取 `subprojects/wayland-protocols.wrap` 验证，确认其中 `source_url` 和 `source_hash` 正确。

## 潜在风险
无。该修改使 sp4 Dockerfile 与已验证可工作的 sp3 Dockerfile 模式一致，仅移除了错误的覆盖操作，不影响其他构建步骤。