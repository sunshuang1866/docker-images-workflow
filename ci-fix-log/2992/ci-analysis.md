# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: `Curl error (92)`, `HTTP/2 framing layer`, `INTERNAL_ERROR`, `No more mirrors to try`, `stream was not closed cleanly`

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库服务器在处理 HTTP/2 请求时多次返回 `INTERNAL_ERROR`（Curl error 92），导致 dnf 下载 gcc、gcc-gfortran、glibc-devel、guile 等多个 RPM 包失败，所有镜像重试耗尽后构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile 和若干元数据文件更新，变更内容本身正确。失败是 openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 协议层问题——这是一个服务端基础设施故障，而非代码错误。Dockerfile 中 `dnf install` 所列的包名、仓库配置均无问题；两份构建阶段（builder #8 和 stage-1 #7）在下载不同包时均遭遇了相同的 `INTERNAL_ERROR`，进一步佐证这是仓库侧问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败为 openEuler 24.03-LTS-SP4 软件仓库服务器的临时性 HTTP/2 故障，属于 infra-error。在仓库服务恢复后重新触发 CI 构建即可。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 当前是否正常运行（HTTP/2 服务是否已恢复）。
- 如果同一时间段其他 PR 的 24.03-LTS-SP4 构建也失败且报相同错误，可进一步确认是仓库侧问题。
