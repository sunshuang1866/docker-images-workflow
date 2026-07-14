# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson Wrap 哈希不匹配
- 新模式症状关键词: Incorrect hash for source, subproject, wayland-protocols, meson.build, wrap

## 根因分析

### 直接错误
```
#12 6.552 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 6.552 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 6.552 Looking for a fallback subproject for the dependency wayland-protocols
#12 6.552 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 6.552 Downloading file of unknown size.
#12 6.552 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 6.552 ERROR: Subproject wayland-protocols is buildable: NO
#12 6.552
#12 6.552 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 6.552  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 6.552  9f0894c55525fe73281efde3427b68b02605f9c350f6698ea072ba4615dbdd7e actual.
```

### 根因定位
- 失败位置: `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile:26`（`meson setup build` 步骤），对应 `meson.build:2013:21`
- 失败原因: openEuler 24.03-LTS-SP4 系统中 `wayland-devel` 提供 wayland-protocols 1.33，不满足 mesa 25.3.4 对 wayland-protocols >= 1.41 的版本要求；meson 回退到从 GitLab 下载 wayland-protocols 1.41 作为 fallback 子项目，但 mesa 源码包内 `subprojects/wayland-protocols.wrap` 中硬编码的 SHA256 哈希值与 GitLab 自动生成的 tarball 实际哈希不匹配。

### 与 PR 变更的关联
PR 新增的 Dockerfile 安装了 `wayland-devel`，它提供了 wayland-protocols 1.33（在 openEuler 24.03-LTS-SP4 仓库中），但 mesa 25.3.4 要求 >= 1.41。该版本差距触发 meson 下载 fallback 子项目，而 .wrap 文件中的固定 SHA256 与 GitLab tarball 实际哈希不一致（GitLab `/-/releases/.../downloads/` 路径生成的 tarball 哈希值不具确定性），导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 `meson setup` 之前，通过 dnf 安装一个满足 >= 1.41 要求的 wayland-protocols 版本。如果 openEuler 24.03-LTS-SP4 的官方/EPOL 仓库中不提供 >= 1.41 的 wayland-protocols-devel RPM 包，则改为从源码手动构建安装 wayland-protocols 1.41（下载、meson setup、meson install），使其作为系统依赖满足 meson 对 wayland-protocols 的 pkg-config 检测，从而避免触发 fallback 子项目下载和哈希校验。

### 方向 2（置信度: 中）
修改 mesa 源码包中 `subprojects/wayland-protocols.wrap` 文件，将 `source_hash` 更新为实际下载到的 tarball 的 SHA256 值（`9f0894c55525fe73281efde3427b68b02605f9c350f6698ea072ba4615dbdd7e`），使其通过 meson 的哈希校验。但此方案不稳定——GitLab 自动生成的 tarball 哈希值可能因服务器端变化而再次变更。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 EPOL 仓库中是否有 wayland-protocols-devel >= 1.41 的 RPM 包可用
- 如果有，确认其包名是否为 `wayland-protocols-devel` 还是其他名称
- 如果无可用 RPM，需确认从源码构建 wayland-protocols 1.41 所需的额外构建依赖（meson、ninja 已安装，需确认是否还需要额外的 -devel 包）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需特殊验证——修复方向不涉及 patch 上游源码。若采用方向 2（修改 .wrap 哈希），需从 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 重新下载 tarball 并计算 SHA256，确认更新后的哈希值匹配。
