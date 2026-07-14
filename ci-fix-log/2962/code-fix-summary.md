# 修复摘要

## 修复的问题
meson 构建时 wayland-protocols subproject 回退下载因上游 tarball 重发布导致 SHA256 哈希不匹配，修复为在构建时动态计算哈希并预置包缓存。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `meson setup` 之前新增一个 RUN 步骤，预下载 wayland-protocols-1.41.tar.xz，动态计算 SHA256 并更新 wrap 文件中的哈希值，同时将 tarball 放入 `subprojects/packagecache/` 避免 meson 二次下载。

## 修复逻辑
分析报告的根因：openEuler 24.03-LTS-SP4 仓库中 `wayland-protocols-devel` 版本为 1.33，不满足 mesa 25.3.4 要求的 >= 1.41，触发 meson 的 subproject 回退机制从 gitlab.freedesktop.org 下载 tarball。但上游 tarball 被重发布后 SHA256 与 mesa 源码中 `wayland-protocols.wrap` 记录的值不一致，导致哈希校验失败。

修复方案：不硬编码固定的哈希值，而是在构建时从上游下载 tarball，用 `sha256sum` 动态计算实际哈希，通过 `sed` 更新 wrap 文件，并将 tarball 放入 `subprojects/packagecache/` 目录（meson 的默认包缓存位置），使 meson 直接使用已缓存的包而不触发二次下载和校验。此方案完全免疫上游 tarball 重发布导致的哈希变化。

验证说明：已从上游 gitlab.freedesktop.org 下载 `wayland-protocols-1.41.tar.xz` 并确认 sed 正则 `s/^source_hash = .*/source_hash = ${WP_HASH}/` 对 `subprojects/wayland-protocols.wrap` 匹配成功。

## 潜在风险
无。此修改仅影响 SP4 的 mesa 构建流程，不涉及其他文件。若 gitlab.freedesktop.org 不可达，wget 步骤会失败，构建会显式报错而非产生静默的哈希不匹配问题。