# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, openEuler repo, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 OS 仓库镜像在 HTTP/2 协议层反复出现 `INTERNAL_ERROR (err 2)` 流错误，导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包多次重试后仍无法下载，`dnf install` 最终因所有镜像均已尝试过而失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR #2992 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（Dockerfile 语法和包名均正确）及对应的 README、image-info.yml、meta.yml 元数据文件。真正的失败原因是 CI 构建环境中 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端异常，属于基础设施故障，即使回退 PR 代码也无法解决。

两个构建阶段（`#7` stage-1 和 `#8` builder）均在不同 HTTP/2 流上遭遇相同的 `INTERNAL_ERROR`，说明这是仓库镜像端的系统性问题而非偶发网络抖动。

## 修复方向

### 方向 1（置信度: 中）
重试 CI 构建。HTTP/2 流错误属于仓库镜像端的临时性协议故障，可能已自行恢复。在无代码变更的情况下重新触发 CI pipeline，若仓库镜像恢复正常则构建应能通过。

### 方向 2（置信度: 低）
若多次重试均失败且仓库镜像持续异常，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 或 `--setopt` 将 dnf 的 HTTP 协议降级为 HTTP/1.1（如 `--setopt=ip_resolve=4`），或配置备用镜像源绕过问题仓库。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 OS 仓库镜像当前的 HTTP/2 服务状态是否已恢复正常
- 此间其他使用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也遭遇相同错误——若是，可确认为仓库端问题
- `#7` stage-1 阶段虽然同样遭遇 HTTP/2 错误但被 CANCELED 而非直接失败，其是否能独立通过需要单独验证
