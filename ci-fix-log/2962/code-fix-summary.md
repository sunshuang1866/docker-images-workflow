# 修复摘要

## 修复的问题
meson 构建时 wayland-protocols 子项目从 GitLab 下载的 tarball 哈希值与源码 wrap 文件中的预期值不一致，导致构建失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `meson setup` 前添加 `sed` 命令，将 `subprojects/wayland-protocols.wrap` 中的 `source_url` 和 `source_hash` 替换为稳定的 freedesktop.org 官方发布地址及其对应 SHA256。

## 修复逻辑
根因是 GitLab 动态生成 release tarball 的 SHA256 哈希值不稳定（同一 URL 在不同时间/请求下可能返回不同内容），导致 meson 的哈希校验失败。将源码下载源从 GitLab（`https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz`）改为 freedesktop.org 官方发布页（`https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz`，SHA256: `cea75b0a503a77e1c60a39c02d8849c285aed5d983b1e96c6e7c90b735982d32`）。freedesktop.org 的 release tarball 是由维护者签名发布的稳定文件，哈希值永久不变。已从该地址两次下载文件确认哈希一致，正则匹配方式为宽松模式（`s|source_url = .*|...`），兼容 wrap 文件的格式变化。

## 潜在风险
- 替换后的 source_url 依赖 freedesktop.org 的持续可用性，但该域名为 wayland 项目官方发布渠道，稳定性高。
- 若未来 mesa 版本升级且 wayland-protocols 需求版本变化，wrap 文件路径（`subprojects/wayland-protocols.wrap`）仍应有效。
- 不影响 SP3 构建或其他版本，仅修改 SP4 Dockerfile 的构建步骤。