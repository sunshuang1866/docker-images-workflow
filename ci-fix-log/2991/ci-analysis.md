# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 仓库 aarch64 镜像服务器多次返回 HTTP/2 协议层内部错误（`Curl error (92)`），导致 `git-core`、`gcc-c++`、`guile` 等多个 aarch64 RPM 包下载失败。最终 `guile` 包的下载在所有镜像重试后均未成功，`dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容正确——仅包含基本的 `dnf install 编译依赖 → git clone vvenc 源码 → cmake 构建` 流程，无语法错误或逻辑问题。失败纯粹是 openEuler 24.03-LTS-SP4 aarch64 仓库服务器在构建时段出现了 HTTP/2 协议层故障，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 这是一个临时性的网络/镜像站基础设施问题。`Curl error (92)` 和 `HTTP/2 stream ... INTERNAL_ERROR` 指示服务器端 HTTP/2 协议栈存在间歇性故障。在镜像站服务恢复正常后，重新触发 CI 构建（Re-run）大概率可以通过。无需修改任何代码。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库镜像站当前是否已恢复正常（可在浏览器或 curl 中手动测试下载一个 aarch64 RPM 包）。
- 如果该问题频繁复现，考虑报告给 openEuler 镜像站维护团队排查 HTTP/2 服务端协议实现。
