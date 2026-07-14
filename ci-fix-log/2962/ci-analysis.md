# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson子项目下载404
- 新模式症状关键词: HTTP Error 404: Not Found, wayland-protocols, meson.build, could not get, subprojects

## 根因分析

### 直接错误
```
#12 38.11 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 38.11 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 38.11 Looking for a fallback subproject for the dependency wayland-protocols
#12 38.11 Downloading wayland-protocols source from https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz
#12 38.11 HTTP Error 404: Not Found
#12 38.11 WARNING: failed to download with error: could not get https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz; is the internet available?. Trying after a delay...
#12 38.11 ERROR: Subproject wayland-protocols is buildable: NO
#12 38.11 meson.build:2013:21: ERROR: could not get https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz; is the internet available?
```

### 根因定位
- 失败位置: `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile:26-56`
- 失败原因: PR 新增的 Dockerfile（行 26-56 的 RUN 指令）中通过 `sed` 显式设置了 wayland-protocols 的 `source_url` 为 `https://wayland.freedesktop.org/releases/wayland-protocols-1.41.tar.xz`，该 URL 实际返回 HTTP 404，导致 meson 配置阶段无法下载 wayland-protocols 1.41 子项目依赖。mesa 25.3.4 要求 wayland-protocols >= 1.41，而 openEuler 24.03-LTS-SP4 系统包只安装了 1.33 版本，meson 尝试以子项目方式回退下载时失败。

### 与 PR 变更的关联
直接由 PR 新增的 Dockerfile 引起。Dockerfile 中的两行 `sed` 命令覆盖了 mesa 上游 wrap 文件中 wayland-protocols 的 `source_url` 和 `source_hash`，将下载地址硬编码指向了一个不存在的 URL（404）。该 URL 指向的 `wayland-protocols-1.41.tar.xz` 在 `wayland.freedesktop.org/releases/` 路径下不存在。

## 修复方向

### 方向 1（置信度: 高）
调查 wayland-protocols 1.41 的正确下载地址（可能在 GitLab 归档路径如 `gitlab.freedesktop.org/wayland/wayland-protocols/-/archive/1.41/`，或 freedesktop.org 使用不同路径格式），然后将 Dockerfile 中 sed 命令的 `source_url` 修正为真实可下载的 URL，同时更新对应的 `source_hash`。

### 方向 2（置信度: 高）
移除 Dockerfile 中对 `source_url` 和 `source_hash` 的 sed 覆盖操作，改为通过 `dnf install` 安装满足版本要求的 wayland-protocols-devel 系统包（需确认 openEuler 24.03-LTS-SP4 仓库是否提供 >= 1.41 的版本）。如果仓库版本不足，则保留 sed 覆盖方案但修正为正确 URL。

## 需要进一步确认的点
- wayland-protocols 1.41 的真实可下载地址是什么（URL 格式可能与 Dockerfile 中的 `wayland.freedesktop.org/releases/` 路径不同）
- wayland-protocols 1.41 对应的 sha256 hash 值是否与 Dockerfile 中写的 `cea75b0a503a77e1c60a39c02d8849c285aed5d983b1e96c6e7c90b735982d32` 一致
- openEuler 24.03-LTS-SP4 仓库中是否提供了 `wayland-protocols-devel >= 1.41` 的 RPM 包（可以替代子项目下载方案）

## 修复验证要求
code-fixer 必须验证修正后的 `source_url` 确实可下载且返回正确的 tar.xz 文件（非 HTML 页面），并且 `source_hash` 与下载文件的实际 sha256 值一致。建议使用 `curl -sI` 或 `wget --spider` 预检 URL 可达性。若改用 dnf 安装系统包方案，需验证 `dnf install wayland-protocols-devel` 在 openEuler 24.03-LTS-SP4 基础镜像中能安装 >= 1.41 版本。
