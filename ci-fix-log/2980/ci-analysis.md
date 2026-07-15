# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 Repo镜像流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf, repo.***.org

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 dnf 从 `repo.****.org` (openEuler 仓库镜像) 下载 RPM 包时遭遇 HTTP/2 stream 错误 (`Curl error (92)`)，多个包（cmake-data、git-core、gcc-c++）下载失败，其中 gcc-c++ 在所有镜像重试后仍不可达，导致整个 `dnf install` 命令退出码为 1，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 无关。** 此次 PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、包名列表完整，且未涉及任何仓库源配置修改。失败完全由 `repo.****.org` 镜像站在构建时的 HTTP/2 传输层临时故障引起（多个不同包的 HTTP/2 stream 均报告 `INTERNAL_ERROR`）。这是 CI 基础设施侧的瞬态网络问题，同类镜像在正常时段构建即可通过。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI。** 该失败为 openEuler 仓库镜像 HTTP/2 传输层临时故障导致的 `infra-error`，与 PR 代码变更无关。Code Fixer 无需对 Dockerfile 做任何修改，直接触发一次 CI 重新构建即可。若再次失败且错误不同，再另行分析。

## 需要进一步确认的点
- 无需进一步确认。日志中 HTTP/2 流错误（err 2: INTERNAL_ERROR）和 `No more mirrors to try` 均指向 repo 镜像服务端瞬时问题，证据明确且与 PR diff 无关联。
