# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）的 HTTP/2 服务端在传输大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB、glibc-devel 2MB）时频繁出现 `HTTP/2 stream INTERNAL_ERROR`，curl 重试所有可用镜像后仍全部失败，导致 `dnf install` 无法完成包下载。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的改动仅为新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 语法正确（`dnf install` 包列表、`sed` 编译配置改编、`make noGUI` 构建命令均无误）。失败发生在 CI 基础设施层面——openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端不稳定，导致 RPM 包下载阶段失败。日志中可见所有下载错误均为 `[MIRROR]` 级别的网络传输错误，且多个独立的镜像源均返回相同的 HTTP/2 流错误。

## 修复方向

### 方向 1（置信度: 低）
**等待仓库恢复后重试**。该失败为 openEuler 24.03-LTS-SP4 官方仓库的 HTTP/2 服务端临时性故障，与 PR 代码无关。可等待仓库服务恢复后重新触发 CI 构建。如果该错误持续出现，建议向 openEuler 基础设施团队报告仓库 HTTP/2 服务端稳定性问题。

### 方向 2（置信度: 低）
**若需规避仓库不稳定**，可在 Dockerfile 的 `dnf install` 命令前添加代理/缓存层或切换到备用镜像源，但这属于 CI 基础设施的全局配置变更，不应在单个 Dockerfile 中处理。

## 需要进一步确认的点
- 该仓库的 HTTP/2 问题是否为持续性故障还是偶发性波动：可通过重试 CI 构建来验证
- openEuler 24.03-LTS-SP4 仓库是否有已知的 HTTP/2 服务端 bug 或维护窗口
- 同仓库中其他使用 24.03-lts-sp4 基础镜像的 Dockerfile 是否也遇到相同的下载失败
