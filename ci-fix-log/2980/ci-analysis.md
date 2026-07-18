# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像站流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, err 2, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像站在 HTTP/2 协议层返回 `INTERNAL_ERROR`（Curl error 92），导致多个 RPM 包下载中断。虽然 cmake-data 和 git-core 在重试后成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13 MB）在两次尝试后均失败，已无更多镜像可尝试，`dnf install` 最终报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，所列依赖包在仓库中均存在（日志中 `Dependencies resolved` 阶段完整列出了所有 258 个待安装包）。失败是仓库镜像站 HTTP/2 传输层的网络基础设施问题，不是 Dockerfile 或代码层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 这是一个典型的 `infra-error`——仓库镜像站 HTTP/2 传输层出现间歇性错误。cmake-data 和 git-core 在重试后成功下载，说明此问题为瞬时性网络抖动。推荐操作：直接触发 CI 重新运行该 job，大概率可自行恢复。

### 方向 2（置信度: 低）
**若反复失败，考虑为 dnf 降级到 HTTP/1.1 或换源。** 如果重试多次仍失败，可尝试在 Dockerfile 中为 `dnf` 配置禁用 HTTP/2（`http2=false`）或更换仓库源 URL，但这属于规避方案，不是根因修复。

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像站在该时间段的 HTTP/2 服务稳定性状态
- 确认是否只有 24.03-LTS-SP4 的仓库镜像受影响，还是多个 SP 版本均有此问题
- 确认 aarch64 架构的同 PR 构建是否也出现相同错误（若 aarch64 构建设备正常，本失败可进一步确认是 x86_64 仓库镜像的瞬时问题）

## 修复验证要求
（无 — 本失败为 infra-error，无需 code-fixer 介入）
