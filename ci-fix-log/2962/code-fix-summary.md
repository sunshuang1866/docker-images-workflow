# 修复摘要

## 修复的问题
Mesa 25.3.4 构建时 meson 子项目 wayland-protocols 下载 hash 不匹配，meson 配置阶段失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `meson setup` 之前添加 `sed` 命令，为 `subprojects/wayland-protocols.wrap` 文件插入 `source_fallback_url`，指向 wrapdb 在 GitHub 上的托管版本。

## 修复逻辑
CI 构建时 wayland-protocols-1.41 从 GitLab 下载得到的文件 SHA256 与 Mesa 25.3.4 wrap 文件中记录的 hash 不匹配。meson 的 wrap 系统支持 `source_fallback_url` 字段作为备用下载源——当主下载源（GitLab）失败或 hash 不一致时，自动回退到 fallback URL。

已验证:
1. 从上游 Mesa 25.3.4 源码包获取 `subprojects/wayland-protocols.wrap` 文件，确认当前 `source_hash` 为 `2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b`，与当前 GitLab 发布的 wayland-protocols-1.41.tar.xz 实际 SHA256 一致，正则匹配成功。
2. wrapdb（meson 官方子项目镜像）上 `wayland-protocols_1.41-1` 条目录了相同的 `source_hash`，并提供 GitHub 托管的 fallback URL：`https://github.com/mesonbuild/wrapdb/releases/download/wayland-protocols_1.41-1/wayland-protocols-1.41.tar.xz`。
3. 在内存中用实际 wrap 文件内容测试了 `sed` 命令，确认能正确插入 `source_fallback_url` 行。

当 GitLab 端文件再次出现 hash 变更时，meson 将自动回退到 wrapdb 的 GitHub 托管版本，构建可继续。

## 潜在风险
- fallback URL 指向 wrapdb 的 GitHub release 文件，该文件由 mesonbuild 组织维护，长期可用性取决于 mesonbuild/wrapdb 仓库的稳定性。若该仓库清理旧版本，fallback 将失效，届时需要更新为新的 fallback URL 或等待上游修复。
- 若 fallback URL 对应文件的 hash 也与 wrap 文件不一致（极低概率），meson 仍会报错，但不会引入错误构建。