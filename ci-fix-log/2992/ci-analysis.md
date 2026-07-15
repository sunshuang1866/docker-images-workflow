# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 阶段，builder stage）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 x86_64 构建节点上下载 RPM 包时反复出现 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR`），dnf 多次重试不同 stream 仍失败，最终因所有镜像均不可用而报错退出。多个包受影响（`gcc-gfortran`、`guile`、`gcc`），其中 `gcc` 包（34MB）在所有 stream 尝试后彻底失败。

### 与 PR 变更的关联
与 PR 代码变更**无直接关联**。此为 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 传输不稳定）。PR 新增的 Dockerfile 本身语法和逻辑正确，构建失败纯粹因为构建时仓库镜像服务端出现 HTTP/2 协议层内部错误，导致较大 RPM 包下载中断。此问题在重新触发 CI 后可能自动消失。

## 修复方向

### 方向 1（置信度: 低 — 此为非修复方向，仅作说明）
**无需修改代码**。此失败属于网络/仓库基础设施瞬时故障，建议重试 CI（retrigger build）。若重试后仍然失败，需排查 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 配置或网络链路稳定性。

## 需要进一步确认的点
- 在非故障时段重新触发 CI 构建，确认该 Dockerfile 能否正常通过（预期可以）。
- 若反复失败，需联系 openEuler 24.03-LTS-SP4 镜像仓库运维方，确认 `repo.****.org` 的 HTTP/2 服务端是否存在已知问题。
- 检查构建节点到仓库镜像之间的网络链路是否存在丢包或中间代理干扰 HTTP/2 帧传输。
