# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，repo 镜像服务器多次返回 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`，`INTERNAL_ERROR`）。多个包（cmake-data、git-core、gcc-c++）均受此影响，其中 cmake-data 和 git-core 在重试后成功下载，但 gcc-c++（13 MB）经过两次重试均失败并耗尽所有镜像重试次数，最终导致整个 `dnf install` 步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了一个标准的 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，其中的 `dnf install` 命令写法与同类 Dockerfile 一致，没有语法错误或依赖包名问题。失败原因是 openEuler 24.03-LTS-SP4 仓库镜像服务器在下载时段出现的 HTTP/2 协议层故障，属 CI 基础设施/网络问题。PR 的 Dockerfile 代码本身没有缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 openEuler 仓库镜像服务器的 HTTP/2 协议层瞬时故障，属于短暂性网络问题。gcc-c++ 包下载在第一次尝试时 HTTP/2 stream 65 报 `INTERNAL_ERROR`，重试时 stream 83 再次报同样错误，表明服务器侧在处理大文件（13 MB）的 HTTP/2 多路复用流时存在间歇性不稳定。重试 CI 工作流大概率会成功，因为其他受影响的包（cmake-data、git-core）在重试后均成功下载。

### 方向 2（置信度: 中）
**若多次重试仍失败，考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt=fastestmirror=true` 或切换到 HTTP/1.1 下载。** 如果 openEuler 仓库服务器持续存在 HTTP/2 协议问题，可通过在 Dockerfile 中禁用 dnf 的 HTTP/2（如设置 `ip_resolve=4` 或配置 curl 后端参数）绕过。但此操作仅应在确认问题持续复现后才进行，不应作为首次修复手段。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像服务器在 CI 失败时段是否有已知的服务降级或维护事件。
- 确认其他 PR 在同时段构建 24.03-lts-sp4 镜像时是否也遇到相同的 HTTP/2 流错误（判断是否为系统性 repo 问题）。
- 该 runner（`ecs-build-docker-x86-03-sp`）的网络到 repo 镜像之间的路径是否稳定。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需。本次失败为 infra-error，不涉及代码修改或正则 patch。
