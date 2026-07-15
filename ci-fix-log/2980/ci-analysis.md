# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success

#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像下载多个软件包时，curl 遇到 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`）。`cmake-data` 和 `git-core` 在首次失败后通过重试成功下载，但 `gcc-c++` 两次尝试均失败，触发 dnf 放弃所有镜像源，构建终止。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 新增了一个标准 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令语法正确、依赖包名称完整。失败完全由 CI 仓库镜像 `repo.****.org` 的 HTTP/2 协议层不稳定导致，属于基础设施层面的网络问题。

## 修复方向

### 方向 1（置信度: 低）
**重新触发 CI 构建**。HTTP/2 流错误为典型的网络瞬态故障，`repo.****.org` 镜像服务器可能在构建时出现了临时的 HTTP/2 协议层问题。重试构建大概率可以成功（日志中 `cmake-data` 和 `git-core` 在 MIRROR 重试后均成功下载，仅 `gcc-c++` 多次重试仍失败）。

### 方向 2（置信度: 低）
**更换 dnf 镜像源**。如果该 SP4 镜像持续不稳定，可在 Dockerfile 的 `dnf install` 前添加 `sed` 替换 `/etc/yum.repos.d/` 中的 baseurl 为其他已知稳定的镜像源。但这需要确认 CI 环境中是否有其他可用的 SP4 镜像，且本质上是绕过而非修复基础设施问题。

## 需要进一步确认的点
1. **镜像仓库健康状态**：`repo.****.org` 是否在同一时间段有其他项目也遇到了类似的 HTTP/2 流错误？如果是孤立事件，重试即可解决；如果是持续性的仓库问题，需要仓库运维排查。
2. **其他已存在的 SP4 Dockerfile 是否也失败**：检查同 PR 批次或近期其他 PR 中涉及 `24.03-lts-sp4` 的构建是否也出现了相同的 Curl error (92)。如果仅此 PR 失败，说明是瞬态网络抖动；若多个 PR 都失败，说明 SP4 镜像仓库存在持续性问题。
3. **Dockerfile 本身的依赖包是否正确**：虽然当前失败是 infra-error，但若重试后进入编译阶段发现其他构建错误（如缺少依赖），则需依据模式10（缺少构建依赖）进行排查。本次 PR 的 dnf install 列表来自已有 sp3 版本或类似镜像，但 GrADS 编译可能需要额外的依赖（如 `libXaw-devel` 等已列出，但需确认编译阶段是否通过）。
