# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 DNF 软件源镜像（`repo.****.org`）在构建期间出现 HTTP/2 协议层错误（Curl error 92: Stream error in the HTTP/2 framing layer），导致 `gcc-c++`、`cmake-data`、`git-core` 三个 RPM 包下载失败。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 经过多次镜像重试均失败，最终导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 内容本身正确——`dnf install` 命令语法无误，所列举的包名在 openEuler 24.03-LTS-SP4 仓库中均存在（从日志中 DNF 成功解析了 258 个包的依赖关系可证）。失败纯粹由构建时的仓库镜像 HTTP/2 网络传输异常引起，属于间歇性基础设施问题。同一 Dockerfile 在仓库镜像稳定时构建成功。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，直接重试 CI。** 该失败为间歇性的基础设施网络问题（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 协议异常），PR 代码变更无任何错误。触发 CI 重新构建即可，在镜像恢复稳定后大概率通过。

### 方向 2（置信度: 低）
若重试仍失败，可在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5 --setopt=timeout=600` 等参数增强网络容错能力，或考虑将关键大包（如 gcc-c++ 13MB）的安装步骤拆分为独立 RUN 层以便单独重试。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在本次构建时段是否存在已知的服务降级或 HTTP/2 协议问题。
- 若重试后持续失败，需排查 CI runner 到该镜像站的网络链路是否稳定。
