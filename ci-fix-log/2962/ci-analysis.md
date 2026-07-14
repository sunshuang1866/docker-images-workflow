# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson子项目哈希不匹配
- 新模式症状关键词: Incorrect hash for source, subproject, wayland-protocols, meson.build

## 根因分析

### 直接错误
```
#12 6.362 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 6.362 Looking for a fallback subproject for the dependency wayland-protocols
#12 6.362 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 6.362 Downloading file of unknown size.
#12 6.362 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 6.362 ERROR: Subproject wayland-protocols is buildable: NO
#12 6.362 
#12 6.362 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 6.362  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 6.362  5c218e963a229164e90a729084c8b8698784c88bcb5654b247f01ff6c4cbb2fe actual.
```

### 根因定位
- 失败位置: `Dockerfile:26-54`（`meson setup build` 步骤）
- 失败原因: meson 构建系统在配置阶段因系统未安装 `wayland-protocols`（pkg-config 查找失败），回落至下载子项目（subproject）。mesa 25.3.4 源码内 `subprojects/wayland-protocols.wrap` 文件中记录的 SHA256 哈希值与 `gitlab.freedesktop.org` 当前提供的 `wayland-protocols-1.41.tar.xz` 实际哈希值不匹配，导致 meson 哈希校验失败，构建终止。

### 与 PR 变更的关联
PR 新增了一个完整的 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`），该 Dockerfile 中 `dnf install` 已包含 `wayland-devel` 但未包含 `wayland-protocols-devel`。meson 配置时找不到系统级 `wayland-protocols` pkg-config 文件，被迫从网络下载子项目，触发哈希校验失败。**此问题并非上游 mesa 源码有 bug，而是 Dockerfile 遗漏了编译依赖包，导致 meson 走了非预期的子项目下载路径。** PR 其余改动（README.md、image-info.yml、meta.yml）仅涉及元数据更新，与构建失败无关。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 命令中补充 `wayland-protocols-devel` 包，使 meson 能够通过 pkg-config 发现系统已安装的 wayland-protocols，从而跳过子项目下载和哈希校验步骤。同时也建议检查同一条 `dnf install` 中是否存在 `pkgconfig` 拼写错误（应为 `pkgconfig` 或 `pkg-config`），该错误可能导致 meson 的 pkg-config 依赖查找功能异常。

### 方向 2（置信度: 中）
如果 `wayland-protocols-devel` 在 openEuler 24.03-LTS-SP4 仓库中不可用或版本不兼容，可考虑在 Dockerfile 中用 `wget` 手动下载与 wrap 文件哈希匹配的 wayland-protocols-1.41.tar.xz 版本，或在 meson setup 时传递 `-Dwayland-protocols:default_library=static` 等参数绕过子项目下载。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库中是否存在 `wayland-protocols-devel` 包及其版本是否 >=1.31（mesa 25.3.4 的最低要求）
- Dockerfile 中 `pkgconfig` 是否为笔误（正确包名通常为 `pkgconfig` 或 `pkg-config`），需确认 openEuler 中的确切包名
- 上游 mesa 25.3.4 的 `subprojects/wayland-protocols.wrap` 中记录的哈希对应的是否为 wayland-protocols 1.41 的原始发布版本，还是 upstream 后续重新发布了同名版本

## 修复验证要求
- code-fixer 必须确认 `wayland-protocols-devel` 包在 `openeuler:24.03-lts-sp4` 基础镜像中的确切包名和可用性后再修改 Dockerfile
- 修复后需在 CI 环境中完整执行 `meson setup build` 至编译完成，验证 wayland-protocols 不再触发子项目下载路径
