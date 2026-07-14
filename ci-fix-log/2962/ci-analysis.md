# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson wrap文件hash不匹配
- 新模式症状关键词: Incorrect hash for source, subproject, meson.build, wayland-protocols, expected, actual

## 根因分析

### 直接错误
```
#12 5.418 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 5.418 Downloading file of unknown size.
#12 5.418 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 5.418 ERROR: Subproject wayland-protocols is buildable: NO
#12 5.418
#12 5.418 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 5.418  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 5.418  a802b63e0000e8b87004f6c763faf2f21ba0f660b5de0b7025ae5d2c369a001b actual.
```

### 根因定位
- 失败位置: Dockerfile:26-54（`RUN mkdir build && meson setup build ...` 步骤）
- 失败原因: Mesa 25.3.4 源码包内 `subprojects/wayland-protocols.wrap` 文件记录的 wayland-protocols 1.41 SHA256 hash（`2786b6b..`）与从 GitLab 实际下载到的文件 hash（`a802b63..`）不匹配，meson 配置阶段拒绝继续运行。

### 与 PR 变更的关联
PR 新增了 mesa 25.3.4 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。Dockerfile 通过 `wget` 从 `archive.mesa3d.org` 获取 Mesa 25.3.4 官方源码包后运行 `meson setup` 构建，hash 不匹配的根本原因在上游 Mesa 25.3.4 源码的 wrap 文件中——GitLab 端 wayland-protocols 1.41 的 tar.xz 发布文件可能被重新打包或更换，导致实际 hash 与 wrap 文件中记录的期望值不一致。PR 的代码逻辑本身（dnf 依赖安装、meson 参数配置）无缺陷，但该 Dockerfile 是首次提交，因此触发了此问题。已存在的 SP3 版本（`Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile`）使用相同的 Mesa 25.3.4 源码，若 CI 近期未触发其构建，可能同样受此影响。

## 修复方向

### 方向 1（置信度: 中）
在 `meson setup` 之前，用 `sed` 替换 `subprojects/wayland-protocols.wrap` 中的 `source_hash` 值为实际下载得到的 hash `a802b63e0000e8b87004f6c763faf2f21ba0f660b5de0b7025ae5d2c369a001b`。需注意：此 hash 对应的是当前 GitLab 端文件，若上游再次变更，问题将复现。

### 方向 2（置信度: 中）
在 `meson setup` 之前，为 wayland-protocols.wrap 添加 `source_fallback_url` 指向 wrapdb 托管版本（如 `https://wrapdb.mesonbuild.com/v2/wayland-protocols_1.41-3/get_patch`），期望 wrapdb 版本的 hash 与 wrap 文件记录一致。此方向更稳健，因为 wrapdb 专为此类场景设计。

### 方向 3（置信度: 低）
尝试从 openEuler 24.03-LTS-SP4 的 dnf 仓库安装 `wayland-protocols-devel` >= 1.41 版本，让 meson 直接使用系统包而不触发子项目下载。但日志显示系统 wayland-protocols 版本为 1.33，而 meson 要求 >= 1.41，该方向在当前仓库中大概率不可行。

## 需要进一步确认的点
1. 确认 `Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile` 在最近一次 CI 构建中是否也失败——若同样失败，说明此问题为上游普遍性问题；若成功通过，需排查 SP3 构建环境是否有缓存或使用了不同的下载源。
2. 确认 wayland-protocols 1.41 在 GitLab 上的发布文件近期是否被重新打包（检查 GitLab release 页面及 changelog）。
3. 确认 wrapdb（`https://wrapdb.mesonbuild.com/v2/wayland-protocols_1.41-3/get_patch`）提供的 patch/hash 是否与 wrap 文件一致，优先采用 wrapdb 方案。

## 修复验证要求
若修复方向1采用 `sed` 替换 hash，code-fixer 必须在提交前：
1. 手动下载 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz`，计算其 SHA256 hash，确认与日志中的 `a802b63e0000e8b87004f6c763faf2f21ba0f660b5de0b7025ae5d2c369a001b` 一致。
2. 若可能，检查 wrapdb 上 wayland-protocols 1.41 的最新 wrap/patch 是否存在匹配的 hash 记录，优先采用 wrapdb 方案而非硬编码 hash。
