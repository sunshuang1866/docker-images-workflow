# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson wrap 哈希不匹配
- 新模式症状关键词: Incorrect hash for source, wayland-protocols, meson.build, subproject, wrap

## 根因分析

### 直接错误
```
#12 5.822 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 5.822 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 5.822 Looking for a fallback subproject for the dependency wayland-protocols
#12 5.822 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 5.822 Downloading file of unknown size.
#12 5.822 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 5.822 ERROR: Subproject wayland-protocols is buildable: NO
#12 5.822
#12 5.822 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 5.822  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 5.822  5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f actual.
```

### 根因定位
- 失败位置: `meson.build:2013:21`（mesa 上游源码中引用 wayland-protocols 子项目的构建声明）
- 失败原因: mesa 25.3.4 的 `subprojects/wayland-protocols.wrap` 中记录了 `wayland-protocols-1.41.tar.xz` 的预期 SHA256 哈希值，但该文件从 GitLab（`gitlab.freedesktop.org`）下载下来的实际哈希与预期不一致。GitLab 的自动生成 release 归档文件（tarball）因为没有稳定的压缩方式导致校验和每次都可能不同，是 meson wrap 使用 GitLab URL 获取源码时的已知问题。

同时，系统上通过 dnf 安装的 `wayland-protocols` 版本为 1.33，不满足 mesa 25.3.4 要求的 `>= 1.41`，因此 meson 无法使用系统包，只能回退到下载子项目，进而触发了哈希校验失败。

### 与 PR 变更的关联
PR 变更与失败**无直接因果关系**。PR 仅新增了一个 Dockerfile 和更新了元数据文件（README.md、image-info.yml、meta.yml），失败是由 mesa 25.3.4 上游源码包中 `wayland-protocols.wrap` 文件的 SHA256 哈希与 GitLab 动态生成的 tarball 实际哈希不匹配引起的。该问题同样会影响其他使用同一 mesa 版本的构建。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 meson setup 步骤之前，通过 `sed` 修改 `subprojects/wayland-protocols.wrap` 文件，将其中记录的 SHA256 哈希值从旧值更新为当前 tarball 的实际哈希值 `5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f`。

### 方向 2（置信度: 中）
在 Dockerfile 的 `dnf install` 阶段补充安装 `wayland-protocols-devel >= 1.41`，使 meson 直接使用系统包而无需下载子项目。但 openEuler 24.03-LTS-SP4 仓库中 `wayland-protocols-devel` 可用版本为 1.33，需确认是否有 EPOL 或第三方源提供 1.41+ 的 RPM 包。若无可用 RPM 则此方向不可行。

### 方向 3（置信度: 低）
参考 mesa 上游已有的处理方式，在 `wayland-protocols.wrap` 中添加 `source_fallback_url` 指向一个稳定的镜像源（如 `wrapdb.mesonbuild.com` 上的 wayland-protocols 镜像），其 tarball 校验和通常是固定的。但需要确认该 wrapdb 镜像上是否有 1.41 版本的确定字节级备份。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 的 EPOL 或其他第三方源中是否存在 `wayland-protocols-devel >= 1.41` 的 RPM 包，若有则方向 2 为最简洁解法。
2. 同样使用 mesa 25.3.4 的 SP3 Dockerfile 是否也存在此问题（可能 GitLab tarball 哈希在某个时间点发生了变化），需验证 SP3 的构建日志确认。
3. 确认 `wrapdb.mesonbuild.com` 上 wayland-protocols 1.41 的 patch/wrap 文件哈希是否与当前 tarball 一致。

## 修复验证要求
若采用方向 1，code-fixer 需确认：在 Docker 构建环境中实际下载 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 并计算 SHA256，与 wrap 文件中写入的哈希值一致后方可提交。GitLab 动态生成归档文件的校验和可能因 GitLab 版本升级或 git archive 参数变更而再次变化，需在提交前实际验证。
