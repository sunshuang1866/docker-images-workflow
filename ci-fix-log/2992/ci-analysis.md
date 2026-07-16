# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 包仓库（`repo.****.org`）在 2026-07-09 构建时段发生 HTTP/2 传输层协议错误（Curl error 92），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载时遭遇 `HTTP/2 stream not closed cleanly: INTERNAL_ERROR`，dnd 在尝试所有镜像均失败后报告 `No more mirrors to try`，导致 `dnf install` 以 exit code 1 终止。最终错误包为 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`，但此前已有 5 个包在下载时出现过同类 stream 错误。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个符合现有模式（与 sp3 版本完全同构）的 Dockerfile 以及 README、image-info.yml、meta.yml 的文档条目。Dockerfile 语法正确，`dnf install` 命令格式无问题。失败纯粹由 CI 构建环境与 openEuler 24.03-LTS-SP4 软件包仓库之间的 HTTP/2 网络传输故障导致。两个 Docker 构建阶段（builder #8 和 stage-1 #7）均遭遇了同类错误，进一步排除了单个文件下载的偶发性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 构建即可。** 此为 openEuler 24.03-LTS-SP4 镜像仓库的临时性 HTTP/2 传输故障（Curl error 92），非持久性问题。建议在仓库服务恢复后重新触发 CI pipeline。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在 2026-07-09 14:45~15:18 UTC 期间是否存在 HTTP/2 服务端故障或负载过高的情况。
- 如果多次重试后仍持续失败，需排查 CI 构建节点（`ecs-build-docker-x86-03-sp`）与仓库之间的网络链路是否稳定。
