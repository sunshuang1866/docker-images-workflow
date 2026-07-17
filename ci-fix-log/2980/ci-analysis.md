# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, dnf install, gcc-c++

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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 dnf 下载 RPM 包时出现 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个包（cmake-data、git-core、gcc-c++）受影响。`gcc-c++` 在重试耗尽所有镜像后最终下载失败，导致整个 `dnf install` 命令退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套 README、meta.yml、image-info.yml 更新。Dockerfile 中的 `dnf install` 命令语法正确、包列表合理，失败完全源于构建时 openEuler 仓库镜像的 HTTP/2 基础设施临时故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施临时故障（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 流异常），应重新触发 CI 构建。如果重试后仍然失败，需联系 openEuler 基础设施团队排查 `repo.****.org` 镜像服务的 HTTP/2 代理状态。

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像服务在当前时间段是否存在已知的 HTTP/2 协议层故障或维护窗口
- 确认其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 CI job 是否也出现了类似的 `Curl error (92)` 模式，以排除是单次偶发还是持续性故障

## 修复验证要求
（无需填写——此为 infra-error，无需代码修复）
