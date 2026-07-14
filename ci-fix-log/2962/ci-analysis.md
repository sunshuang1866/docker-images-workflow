# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: meson wrap 哈希不匹配
- 新模式症状关键词: Incorrect hash for source, subproject, meson.build, wrap

## 根因分析

### 直接错误
```
#12 10.11 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 10.11 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 10.11 Looking for a fallback subproject for the dependency wayland-protocols
#12 10.11 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 10.11 Downloading file of unknown size.
#12 10.11 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 10.11 ERROR: Subproject wayland-protocols is buildable: NO
#12 10.11 
#12 10.11 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 10.11  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 10.11  079def0400e723b5fd402cc0b8269d9f037c0f46c50a28852d70eb0031c4a344 actual.
#12 ERROR: process "/bin/sh -c mkdir build ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `mesa-25.3.4/subprojects/wayland-protocols.wrap`（wrap 文件内硬编码的 SHA256 哈希）+ `meson.build:2013:21`（触发 subproject 回退的位置）
- 失败原因: 系统安装的 `wayland-protocols` 版本为 1.33，不满足 mesa 25.3.4 要求的 `>= 1.41`，meson 触发 subproject 回退机制从 gitlab.freedesktop.org 下载 `wayland-protocols-1.41.tar.xz`，但下载到的文件 SHA256 与 mesa 源码中 `wayland-protocols.wrap` 内记录的值不匹配——上游 wayland-protocols 项目可能重发布了 1.41 版本的 tarball，导致内容变化而哈希不再吻合。

### 与 PR 变更的关联
**与 PR 改动无直接关系**。PR 仅新增了 mesa 25.3.4 针对 SP4 的 Dockerfile 和元数据条目，Dockerfile 本身的构造逻辑（下载源码 → pip 安装 meson → meson configure + build + install）是常规且正确的。失败根因在于上游生态问题：
1. openEuler 24.03-LTS-SP4 仓库中 `wayland-protocols` 包版本仅为 1.33，不符合 mesa 25.3.4 的最低版本要求（>= 1.41）
2. mesa 25.3.4 源码的 `wayland-protocols.wrap` 中记录的 SHA256 与 gitlab.freedesktop.org 当前提供的 `wayland-protocols-1.41.tar.xz` 不匹配

这不是 PR 逻辑错误，而是 SP4 操作系统仓库中 `wayland-protocols` 版本过旧与上游 tarball 重发布叠加导致的构建环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `meson setup` 之前，通过 `sed` 或脚本更新 `subprojects/wayland-protocols.wrap` 中的 SHA256 哈希值，将其从旧值 `2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b` 替换为当前实际值 `079def0400e723b5fd402cc0b8269d9f037c0f46c50a28852d70eb0031c4a344`。这样 meson 就能通过哈希校验，正常构建 wayland-protocols subproject。

### 方向 2（置信度: 中）
在 `dnf install` 步骤中尝试从 openEuler 24.03-LTS-SP4 的 EPOL 或其他仓库安装更高版本的 `wayland-protocols-devel`（版本需 >= 1.41），使 meson 在系统依赖查找阶段就找到满足要求的版本，避免触发 subproject 回退下载。需先确认 SP4 仓库中是否存在 >= 1.41 的 `wayland-protocols-devel` 包。

## 需要进一步确认的点
1. SP4 仓库或 EPOL 仓库中是否存在 `wayland-protocols-devel >= 1.41` 的包（`dnf list wayland-protocols-devel --showduplicates`）
2. gitlab.freedesktop.org 上 wayland-protocols-1.41 的 tarball 是否确实被重发布过（对比发布时间与 mesa 25.3.4 的 release date）
3. 现有 SP3 的 mesa Dockerfile 是否也在构建时触发同样的 subproject 回退——如果是且构建成功，说明 SP3 的 `wayland-protocols` 系统包版本 >= 1.41，问题仅在 SP4 上出现

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
若采用**方向 1**（修改 wrap 文件中的哈希），code-fixer 必须在提交前：
- 从 gitlab.freedesktop.org 重新下载 `wayland-protocols-1.41.tar.xz`，计算其 SHA256，确认与日志中报告的 `079def0400e723b5fd402cc0b8269d9f037c0f46c50a28852d70eb0031c4a344` 一致
- 若哈希再次发生变化，应改用从 `archive.mesa3d.org` 获取的 mesa 25.3.4 源码包中 `wayland-protocols.wrap` 内的原始哈希为基准，改用 `meson wrap` 的 `source_fallback_url` 指向一个稳定的、哈希不变的归档源（如 meson wrapdb 或 mesa 官方托管）
