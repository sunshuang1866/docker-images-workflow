# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install` 步骤）
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，HTTP/2 传输层多次出现 `INTERNAL_ERROR (err 2)` 流错误。多个关键包（`gcc-gfortran`、`guile`、`gcc`）均遇到该错误，其中 `gcc-12.3.1-110.oe2403sp4.x86_64` 在所有镜像均重试失败后耗尽重试次数，导致整个 `dnf install` 命令以退出码 1 失败。该错误是 openEuler 仓库镜像服务器的 HTTP/2 协议栈问题，非 PR 代码变更所致。

### 与 PR 变更的关联
**与 PR 无关。** PR #2992 的改动仅包括：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行新 Dockerfile）
- 更新 `README.md`、`doc/image-info.yml`、`meta.yml` 的条目

失败发生在 Dockerfile 最基础的 `dnf install` 依赖安装阶段，尚未到达 PR 新增的任何业务逻辑（如 git clone、sed 修改 Makefile、make 编译）。同为 24.03-LTS-SP4 源的另一个并行构建 stage（`#7`，即运行时阶段）也出现了相同类型的 HTTP/2 流错误（`glibc-devel` 和 `gcc-gfortran` 遇到 `Curl error (92)`），只是因为安装的包较少（32 vs 157）侥幸未触发致命失败。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端临时性故障，与 PR 代码完全无关。重新触发 CI 流水线，待镜像站恢复后即可通过。

### 方向 2（置信度: 低）
若重试后仍然失败，可检查 CI runner 所在网络环境到 `repo.****.org` 的连接质量（HTTP/2 兼容性），考虑降级到 HTTP/1.1（在 dnf 配置中设置 `http2=false`）作为 workaround。但此方向仅适用于 CI 基础设施维护场景，不属于 Code Fixer 的修复范畴。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像站）在构建时所处时段的可用性状态
- 确认 CI runner（`ecs-build-docker-x86-03-sp`）所在网络环境与仓库镜像站之间的 HTTP/2 连接稳定性，是否存在中间代理/防火墙干扰 HTTP/2 流的情况
