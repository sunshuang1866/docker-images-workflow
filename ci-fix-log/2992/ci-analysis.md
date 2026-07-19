# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在响应 HTTP/2 请求时发生流级协议错误（`INTERNAL_ERROR`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载均受此影响，最终 `gcc` 包因所有镜像均尝试失败而报 `No more mirrors to try`，`dnf install` 退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（基于 `openeuler/openeuler:24.03-lts-sp4` 基础镜像）、更新了 README.md 和两个元数据文件。失败的直接原因是 openEuler 24.03-LTS-SP4 官方仓库镜像的 HTTP/2 服务端协议错误，属于 CI 基础设施/上游仓库的临时性故障。日志中 `#7`（stage-1 阶段，同样依赖 SP4 仓库）也出现了相同的 `Curl error (92)` 报错（`glibc-devel`、`gcc-gfortran`），进一步证实这是仓库端的系统性问题，而非 Dockerfile 内容错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此为 openEuler 24.03-LTS-SP4 官方软件仓库镜像的临时性 HTTP/2 协议故障（Curl error 92: INTERNAL_ERROR）。应等待上游仓库恢复后重新触发 CI 构建，或联系 openEuler 基础设施团队确认仓库服务状态。若问题持续，可考虑通过 `dnf install` 前添加重试机制（如 `--setopt=retries=10`）或临时切换至备用镜像源来绕过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）的 HTTP/2 服务当前状态是否正常
- 确认该仓库错误是否为持续性问题还是暂时性波动（可查看同一时段其他使用 SP4 基础镜像的 PR 构建状态）
- 确认 `docker.io/openeuler/openeuler:24.03-lts-sp4` 基础镜像内置的 dnf 仓库配置指向的镜像地址是否存在已知故障
