# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方软件包仓库（`repo.****.org`）在 Docker 构建过程中出现间歇性 HTTP/2 流错误（Curl error 92），导致多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）下载中断。其中 `gcc-c++` 在耗尽所有镜像重试后仍无法下载成功，`dnf install` 最终以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 变更仅为新增 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 包列表和构建步骤本身没有语法或逻辑错误。失败完全由 openEuler 24.03-LTS-SP4 软件包仓库镜像的 HTTP/2 传输层不稳定性导致。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施层面的瞬态网络故障（openEuler 仓库镜像 HTTP/2 流中断）。Code Fixer 无需处理，等待仓库镜像恢复稳定后重试构建即可通过。

### 方向 2（置信度: 低）
如果仓库镜像持续不稳定，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries` 参数或 `--setopt=retries=10` 提高下载重试次数，但这属于防御性措施而非根因修复。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）的网络状态是否已恢复，可通过在其他构建任务中重试确认。
2. 若持续出现此类 HTTP/2 流错误，需排查 CI runner 所在网络到 openEuler 仓库之间的 CDN/代理链路是否存在问题。
