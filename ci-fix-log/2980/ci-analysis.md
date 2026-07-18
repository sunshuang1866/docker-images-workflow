# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing, Stream error, INTERNAL_ERROR, dnf install, repo mirror

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
ERROR: failed to solve: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: Docker 构建在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），其中 gcc-c++ 在所有镜像上均重试失败，导致整个 `dnf install` 命令退出。这是 CI 运行时仓库镜像服务器的瞬时网络/协议问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）并更新 README、image-info.yml、meta.yml 三个元数据文件。新增 Dockerfile 在 `dnf install` 步骤请求的 RPM 包列表与已有 SP3 版本结构一致，无语法错误或包名错误。失败纯粹由 openEuler 仓库镜像在构建期间的 HTTP/2 传输层间歇性故障导致——约 258 个包中绝大部分下载成功，仅个别包因协议错误失败。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为仓库镜像服务器的瞬时 HTTP/2 协议故障（Curl error 92），与 PR 代码完全无关。等待镜像服务恢复后重新触发 CI 构建即可。若多次重试仍失败，可考虑调整 `dnf` 配置降级到 HTTP/1.1（设置 `http2=false` 在 dnf 仓库配置中），绕过 HTTP/2 协议层的不稳定。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在构建时段是否有已知的 HTTP/2 协议问题或服务降级。
- 如果同一仓库的其他镜像（同一 SP4 基础镜像）近期也频繁出现同类 Curl error 92，建议在 CI 侧统一配置 dnf 的 HTTP/2 降级策略。

## 修复验证要求
无需代码修复，仅需重试 CI。若重试后仍失败且确认是仓库服务端持续性问题，建议从 infra 层面调整 dnf 的网络传输配置。
