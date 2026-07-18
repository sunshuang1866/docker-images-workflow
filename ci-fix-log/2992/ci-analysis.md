# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 官方仓库镜像在 HTTP/2 传输层面出现多次流错误（`Curl error 92: INTERNAL_ERROR`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载重试失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64` 耗尽所有镜像后下载失败，导致 Docker 构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml）。失败发生在 `dnf install` 从 openEuler 24.03-LTS-SP4 官方仓库下载 RPM 包的阶段，这是一个 CI 基础设施层面的网络/仓库服务问题，并非 PR 代码逻辑（Dockerfile 语法、依赖声明、构建命令）导致的错误。

值得注意的是：同一次构建中的 stage-1（`#7`）同样遭遇了 `glibc-devel` 和 `gcc-gfortran` 的 HTTP/2 流错误，但经重试后成功；而 builder 阶段（`#8`）下载 `gcc` 包时重试耗尽后彻底失败，表明仓库服务本身存在间歇性不稳定。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性基础设施问题（HTTP/2 流中断），Code Fixer 无需处理。建议触发 CI 重新运行（retry），等待仓库服务恢复后重试即可。若多次重试均失败，需联系 openEuler 仓库维护团队排查镜像站 HTTP/2 服务稳定性。

### 方向 2（置信度: 低）
若仓库镜像问题长期无法解决，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt=timeout=60 --save` 或通过 `echo 'timeout=60' >> /etc/dnf/dnf.conf` 增大下载超时，但这只能缓解问题，无法根治 HTTP/2 流层面的底层错误。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 服务状态是否正常，建议联系仓库运维团队确认镜像站健康状态。
- 是否有其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 在同一时间段遭遇相同错误，以确认是否为仓库侧系统性故障。

## 修复验证要求
无需验证（infra-error，与 PR 代码无关）。
