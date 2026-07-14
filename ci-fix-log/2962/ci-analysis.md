# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: meson wrap 子项目 hash 不匹配
- 新模式症状关键词: Incorrect hash for source, Subproject is buildable: NO, meson.build, wayland-protocols, wrap

## 根因分析

### 直接错误
```
#12 6.410 ERROR: Subproject wayland-protocols is buildable: NO
#12 6.410 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 6.410  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 6.410  993ff8372bdddb83f766db5a9f2214baae4845ef610d60026c47689497f33bb6 actual.
```

此前 meson 配置阶段已显示：
```
#12 3.800 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 3.800 Looking for a fallback subproject for the dependency wayland-protocols
#12 6.410 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 6.410 Downloading file of unknown size.
#12 6.410 A fallback URL could be specified using source_fallback_url key in the wrap file
```

### 根因定位
- 失败位置: `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile:26`（`meson setup build` 步骤），具体为 mesa 源码内 `meson.build:2013:21` 触发
- 失败原因: mesa 25.3.4 的 `subprojects/wayland-protocols.wrap` 文件记录了 wayland-protocols 1.41 的预期 SHA256 为 `2786b6b1...`，但从 GitLab 实际下载到的 tarball 内容计算出的 SHA256 为 `993ff837...`，hash 不匹配导致 meson 拒绝继续构建。同时 `wayland-protocols-devel` 系统包未安装，meson 尝试 pkg-config 查找失败后才回退到 wrap 下载。

### 与 PR 变更的关联
不是 PR 代码改动的**直接**问题。PR 新增的 Dockerfile 本身在构建逻辑上正确（安装依赖、下载源码、运行 meson），但遗漏了 `wayland-protocols-devel` 系统包。mesa 上游源码中 `wayland-protocols.wrap` 文件记录的 hash 与 GitLab 当前提供的 tarball 不匹配（上游可能重新打包了同版本号的 tarball），导致 meson wrap 下载校验失败。由于缺少系统级别的 wayland-protocols pkg-config 供应，meson 无法跳过 wrap 下载。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 命令中添加 `wayland-protocols-devel` 包，使 meson 通过 pkg-config 发现已安装的系统级 wayland-protocols，从而跳过 wrap 子项目下载（meson 优先使用系统包，仅在没有系统包时才触发 wrap 下载）。此方案完全规避 hash 不匹配问题。

### 方向 2（置信度: 中）
修正 mesa 源码中 `subprojects/wayland-protocols.wrap` 的 source_hash 字段，将预期值更新为实际 SHA256 `993ff8372bdddb83f766db5a9f2214baae4845ef610d60026c47689497f33bb6`。此方案需要修改上游源码文件，且若 GitLab 再次更新 tarball 可能再次失效，不建议作为首选。

## 需要进一步确认的点
1. 确认 `wayland-protocols-devel` 在 openEuler 24.03-LTS-SP4 仓库中的可用性及包名是否一致。
2. 确认 mesa 25.3.4 的构建配置对 wayland-protocols 的版本要求（如需 ≥ 1.41，而系统包可能提供较低版本）。
