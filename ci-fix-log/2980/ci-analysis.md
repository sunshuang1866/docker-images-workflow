# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), HTTP/2, INTERNAL_ERROR, dnf install, No more mirrors to try, stream error

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
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输层出现流错误（Curl error 92），导致多个 RPM 包下载中断。虽然 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 两次重试均失败，最终因所有镜像尝试完毕而报错，dnf install 以 exit code 1 退出，Docker 构建中止。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个合法的 Dockerfile（安装 openEuler 24.03-LTS-SP4 仓库中真实存在的 RPM 包），以及配套的 README.md、image-info.yml、meta.yml 更新。失败纯属 CI 基础设施中 openEuler 仓库镜像网络传输异常，Dockerfile 语法和包名均正确，重试即可通过。

## 修复方向

### 方向 1（置信度: 高）
无需修改任何代码。这是 openEuler 仓库镜像在构建时段的临时性 HTTP/2 流传输故障，属于 CI 基础设施问题。直接重新触发 CI 构建即可（`retrigger`），大概率能自动通过。

## 需要进一步确认的点
无。日志证据充分，错误信息清晰指向 openEuler 仓库镜像的 HTTP/2 传输层问题，与 PR 代码无关。
