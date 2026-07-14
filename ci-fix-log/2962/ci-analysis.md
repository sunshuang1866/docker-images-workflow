# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Meson子项目哈希不匹配
- 新模式症状关键词: Incorrect hash for source, wayland-protocols, expected, actual, subproject, meson.build

## 根因分析

### 直接错误
```
#13 5.402 ERROR: Subproject wayland-protocols is buildable: NO
#13 5.402 meson.build:2013:21: ERROR: Incorrect hash for source:
#13 5.402  5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f expected
#13 5.402  0b6d27e273d2c5a2e76b429d95d0f3e40f0230c6d6addb11f55186871708dd14 actual.
```

### 根因定位
- 失败位置: `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile:28`（`meson setup build` 步骤）
- 失败原因: Mesa 25.3.4 的 meson 构建系统通过 wrap 文件 (`subprojects/wayland-protocols.wrap`) 下载 `wayland-protocols` 1.41 作为子项目依赖。上游 `wayland-protocols` 1.41 的发行包在 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 被重新生成（其内容哈希已变更），mesh 的 wrap 文件中记录的 `source_hash` 与当前实际下载文件的哈希值不一致：

  - **期望哈希**（wrap 文件中记录）：`5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f`
  - **实际哈希**（当前下载文件）：`0b6d27e273d2c5a2e76b429d95d0f3e40f0230c6d6addb11f55186871708dd14`

  此外，CI 执行的 Dockerfile 中额外包含一条 `sed` 命令（CI 日志步骤 `#11 [6/8]`）尝试将 hash 更新为期望值，但该期望值本身就是错误的，因此 `sed` 替换后 hash 仍不匹配。

### 与 PR 变更的关联

**直接关联。** 该 PR 新增了 `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`，其 `meson setup` 步骤触发了 `wayland-protocols` 子项目的 hash 校验失败。此失败并非由 PR 的代码改动逻辑错误引起，而是上游 `wayland-protocols` 1.41 发行包内容被重新发布导致的 hash 变更。任何在同一时期内构建 mesa 25.3.4（含 `-Dplatforms=x11,wayland`）的 Dockerfile 都会遇到相同问题。

**注意：Dockerfile 版本不匹配。** PR diff 中的 Dockerfile（56 行，无 `sed` 步骤）与 CI 实际执行的 Dockerfile（含 `#11 RUN sed -i 's/source_hash = .../.../' subprojects/wayland-protocols.wrap`）不一致。CI 中这条 `sed` 命令使用了与期望值相同（但同样错误）的 hash，说明提交者在 CI 运行前已经发现了 hash 问题并尝试修复，但使用的替换值不正确。需检查仓库中实际提交的 Dockerfile 内容以确认。

## 修复方向

### 方向 1（置信度: 高）
**更新 wayland-protocols wrap 文件中的 hash 为实际值。**

在 Dockerfile 的 `RUN pip3 install` 之后、`meson setup` 之前，用 `sed` 将 `subprojects/wayland-protocols.wrap` 中的 `source_hash` 更新为当前下载文件的实际 SHA256：

- 如果 Dockerfile 中已有 `sed` 命令（如 CI 步骤 `#11` 所示），将其中 hash 从旧值 `5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f` 改为实际值 `0b6d27e273d2c5a2e76b429d95d0f3e40f0230c6d6addb11f55186871708dd14`
- 如果 Dockerfile 中没有这个 `sed` 步骤，新增一条 RUN 指令，在 `meson setup` 之前执行 hash 替换

### 方向 2（置信度: 中）
**替换 wayland-protocols 子项目的下载源或使用已安装的系统版本。**

两个替代思路：
1. 修改 Dockerfile 的 `meson setup` 参数，禁用 wayland 平台支持（将 `-Dplatforms=x11,wayland` 改为 `-Dplatforms=x11`），回避 wayland-protocols 子项目的下载。但这会丢失 wayland 平台功能。
2. 修改 wrap 文件中的下载 URL 或 `source_fallback_url`，指向一个 hash 与期望值匹配的 wayland-protocols 1.41 镜像副本。

## 需要进一步确认的点

1. **Dockerfile 实际内容**：PR diff 显示的 Dockerfile 与 CI 执行的 Dockerfile 存在差异。需确认仓库中 `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile` 的实际提交内容，明确是否已包含 `sed` 修复行及其具体的 hash 值。
2. **wayland-protocols 1.41 上游 repo 是否稳定**：GitLab `freedesktop.org` 上的 release 包是否确实被重新打包（内容变更），还是 GitLab 的下载 URL（`/downloads/wayland-protocols-1.41.tar.xz`）本身不保证内容稳定性？如果是后者，可能需要寻找稳定的下载镜像。
3. **同类 SP3 是否需要修复**：检查 `Others/mesa/25.3.4/24.03-lts-sp3/Dockerfile` 是否也会遇到相同 hash 不匹配问题（如果该 Dockerfile 也包含 `-Dplatforms=x11,wayland` 且未做 hash 修复）。

## 修复验证要求

修复后必须触发 CI 重新构建，确认 `meson setup` 步骤通过且 hash 校验不再报错。由于本次修复涉及修改 `subprojects/wayland-protocols.wrap` 中的 hash 值以匹配上游重新发布的发行包，code-fixer 应在提交前直接从 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 重新下载文件，计算其 SHA256 并比对确认 hash 与修复后的值一致。
