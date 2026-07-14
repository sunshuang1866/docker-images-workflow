# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf, repo mirror, openEuler 24.03

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在本次 CI 运行期间持续出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），导致多个大型包（gcc 34MB、gcc-gfortran 13MB、glibc-devel 2.0MB、guile 6.3MB）下载失败。dnf 重试所有可用镜像后仍无法完成下载，最终构建退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 Dockerfile（`24.03-lts-sp4/Dockerfile`）及配套的元数据/文档条目，Dockerfile 中 `dnf install` 的命令语法和包列表均正确（与同级 `24.03-lts-sp3` 的 Dockerfile 结构一致，仅基础镜像从 `sp3` 升级为 `sp4`）。失败完全由 openEuler 24.03-LTS-SP4 包仓库镜像侧的 HTTP/2 协议层问题引起，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 24.03-LTS-SP4 RPM 仓库镜像的临时性网络/协议故障。应等待仓库镜像恢复后**重新触发 CI 构建**（retry）。如果多次重试均持续失败，则需联系 openEuler 基础设施团队排查镜像站 HTTP/2 配置。

## 需要进一步确认的点
- 其他同样使用 `openEuler:24.03-lts-sp4` 基础镜像的 PR 是否也在此期间失败（如果是，则确认是镜像站全局问题，进一步支持 infra-error 判定）。
- aarch64 构建 job 的日志（如果存在）是否也显示相同的 Curl error (92)，以确认故障是否跨架构影响。
