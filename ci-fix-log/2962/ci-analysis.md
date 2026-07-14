# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson子项目哈希不匹配
- 新模式症状关键词: Incorrect hash for source, meson.build, subproject, wayland-protocols, wrap file, expected, actual

## 根因分析

### 直接错误
```
#12 5.413 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 5.413 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 5.413 Looking for a fallback subproject for the dependency wayland-protocols
#12 5.413 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 5.413 Downloading file of unknown size.
#12 5.413 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 5.413 ERROR: Subproject wayland-protocols is buildable: NO
#12 5.413
#12 5.413 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 5.413  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 5.413  98017f44211931a4ef113caa8559d4105f11313c28c1eabb07586864962a608c actual.
```

### 根因定位
- 失败位置: `meson setup build` 配置阶段，meson.build 第 2013 行触发了 wayland-protocols 子项目的下载与哈希校验
- 失败原因: openEuler 24.03-LTS-SP4 的 dnf 仓库仅提供 `wayland-protocols-devel` 1.33，低于 mesa 25.3.4 要求的 >= 1.41。meson 触发 fallback 从 GitLab 下载 wayland-protocols-1.41.tar.xz，但该下载返回的实际 SHA256 哈希与 mesa 源码中 `subprojects/wayland-protocols.wrap` 文件记录的预期哈希不一致。这是 GitLab 归档下载的已知缺陷——GitLab 动态生成的 release tarball 其哈希值不可靠，可能随时间或请求变化。

### 与 PR 变更的关联
**直接相关**。PR 新增了 mesa 25.3.4 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（全新文件），构建过程中首次触发了该问题。同日存在 SP3 版本的 mesa 25.3.4（`25.3.4/24.03-lts-sp3/Dockerfile`），若 SP3 的 wayland-protocols-devel 版本满足 >= 1.41，则 SP3 构建不会触发 fallback 下载，不会失败。SP4 基础镜像的 wayland-protocols-devel 版本（1.33）过低是直接诱因。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 步骤中，安装满足版本要求（>= 1.41）的 `wayland-protocols-devel` 包，使 meson 直接使用系统安装的 wayland-protocols，无需触发 fallback 子项目下载。需确认 SP4 的 EPOL 或 update 仓库是否有 >= 1.41 的包，或从更高版本源拉取。

### 方向 2（置信度: 中）
在 `meson setup` 之前，用 `sed` 修改 mesa 源码中 `subprojects/wayland-protocols.wrap` 文件里的 `source_hash` 字段，将其更新为当前 GitLab 下载返回的实际哈希值 `98017f44211931a4ef113caa8559d4105f11313c28c1eabb07586864962a608c`。

### 方向 3（置信度: 低）
在 Dockerfile 中手动从其他镜像源（如 freedesktop.org 官方 mirror）下载 wayland-protocols 1.41 的源码包，放入 meson 的 `subprojects/packagecache/` 目录，绕过 meson 的自动下载与哈希校验。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 的 EPOL 或 update dnf 仓库中是否存在 `wayland-protocols-devel >= 1.41`
2. mesa 25.3.4 在 SP3（`25.3.4/24.03-lts-sp3/Dockerfile`）上的构建是否成功，SP3 的 wayland-protocols-devel 版本是多少，以确认方向 1 的可行性
3. `subprojects/wayland-protocols.wrap` 中是否定义了 `source_fallback_url`，可替换为哈希稳定（如 GitHub release）的下载源

## 修复验证要求
若采用方向 2（修改 wrap 文件哈希），code-fixer 必须从 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 重新下载文件，计算其 SHA256 哈希值，确认与 wrap 文件中将写入的值一致后再提交 sed 命令到 Dockerfile。
