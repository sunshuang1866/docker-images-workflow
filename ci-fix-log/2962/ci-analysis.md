# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson子项目哈希不匹配
- 新模式症状关键词: `Incorrect hash for source`, `meson.build`, `wayland-protocols`, `Fallback subproject`, `wrap`

## 根因分析

### 直接错误
```
#12 5.776 Dependency wayland-protocols for host machine found: NO. Found 1.33 but need: '>= 1.41'
#12 5.776 Run-time dependency wayland-protocols found: NO  (tried pkg-config and cmake)
#12 5.776 Looking for a fallback subproject for the dependency wayland-protocols
#12 5.776 Downloading wayland-protocols source from https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 5.776 Downloading file of unknown size.
#12 5.776 A fallback URL could be specified using source_fallback_url key in the wrap file
#12 5.776 ERROR: Subproject wayland-protocols is buildable: NO
#12 5.776 
#12 5.776 meson.build:2013:21: ERROR: Incorrect hash for source:
#12 5.776  2786b6b1b79965e313f2c289c12075b9ed700d41844810c51afda10ee329576b expected
#12 5.776  40314a897d0db2b0ae18d5a47ffdbfdfa4e22da897c618f336e376425b4945d9 actual.
```

### 根因定位
- 失败位置: `meson.build:2013`（mesa 25.3.4 源码中 `subprojects/wayland-protocols.wrap` 引用的 hash 校验逻辑）
- 失败原因: 构建链式失败——① openEuler 24.03-LTS-SP4 通过 dnf 安装的 `wayland-protocols` 版本为 1.33，不满足 mesa 25.3.4 的 `>= 1.41` 最低要求；② meson 回退到下载 wayland-protocols 1.41 作为子项目；③ 下载的 wayland-protocols-1.41.tar.xz 实际 SHA256 哈希（`40314a8...`）与 mesa 源码中 `subprojects/wayland-protocols.wrap` 文件记录的期望哈希（`2786b6b...`）不匹配，触发 meson 哈希校验失败。

### 与 PR 变更的关联

**直接相关**。PR 新增的 Dockerfile 中 `dnf install` 步骤未包含 `wayland-protocols-devel` 包。当前 `dnf install` 列表虽包含 `wayland-devel`，但其依赖的 `wayland-protocols` 在 openEuler 24.03-LTS-SP4 仓库中版本仅为 1.33，不满足 mesa 25.3.4 的 `>= 1.41` 要求。由于系统包版本不足，meson 被迫走子项目下载路径，而 wrap 文件中的哈希值已过时，导致最终失败。

核心矛盾：**mesa 25.3.4 要求 wayland-protocols >= 1.41，但 openEuler 24.03-LTS-SP4 仓库仅提供 1.33，且 meson wrap 文件中 wayland-protocols 1.41 的哈希值已失效**。

## 修复方向

### 方向 1（置信度: 高）
**在 Dockerfile 中安装 `wayland-protocols-devel` 替代下载子项目**

检查 openEuler 24.03-LTS-SP4 仓库中 `wayland-protocols-devel` 的实际可用版本。如果仓库中存在 `>= 1.41` 的版本（通过 EPOL 或其他源），在 `dnf install` 中显式添加 `wayland-protocols-devel`，使 meson 直接使用系统已安装的包，不再触发子项目下载。

### 方向 2（置信度: 高）
**修正 wrap 文件中的哈希值**

在 Dockerfile 中 `meson setup` 前，用 `sed` 将 `subprojects/wayland-protocols.wrap` 中过期的期望哈希替换为实际下载到的哈希（`40314a897d0db2b0ae18d5a47ffdbfdfa4e22da897c618f336e376425b4945d9`），使 meson 子项目下载能通过校验。或者将下载源改为 `source_fallback_url` 指向一个内容稳定的镜像/归档副本。

### 方向 3（置信度: 中）
**启用 EPOL 仓库以获取更新版本的 wayland-protocols**

在 Dockerfile 的 `dnf install` 之前，先启用 EPOL（Extra Packages for openEuler Linux）仓库（`dnf install -y epol-release`），然后再安装 `wayland-protocols-devel`，EPOL 可能提供比 BaseOS 中 1.33 更新的 wayland-protocols 版本。

### 方向 4（置信度: 低）
**禁用 wayland 平台支持**

将 meson 参数 `-Dplatforms=x11,wayland` 改为 `-Dplatforms=x11`，完全跳过 wayland-protocols 依赖。但这会显著改变镜像的功能范围，不推荐。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库（BaseOS + EPOL）中 `wayland-protocols-devel` 的实际最高版本是什么？是否已有 `>= 1.41` 的版本？
2. `gitlab.freedesktop.org` 上 wayland-protocols 1.41 的 tarball 是否被上游重新打包导致哈希变化？还是 wrap 文件中的哈希记录本身就错误？
3. 参考现有的 mesa SP3 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile`），该版本是否也存在同样的 wayland-protocols 版本问题？如果是，它是如何解决的？

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
若修复方向选择方向 2（sed 修改 wrap 文件哈希），code-fixer 必须在提交前：
- 从 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 下载对应文件，用 `sha256sum` 验证实际哈希值确实为 `40314a897d0db2b0ae18d5a47ffdbfdfa4e22da897c618f336e376425b4945d9`（即日志中报告的 actual 值），确认无误后再写入 wrap 文件。
