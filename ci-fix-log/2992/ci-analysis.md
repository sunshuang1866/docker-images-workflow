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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在构建期间出现 HTTP/2 流层传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个 RPM 包（`gcc-gfortran`、`guile`、`gcc` 等）下载中断。`gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB）在经历多次重试后耗尽所有镜像，最终 `dnf install` 以 exit code 1 失败。注意 `#7`（stage-1 运行时阶段）的 `dnf install` 同样遇到了 `glibc-devel` 和 `gcc-gfortran` 的相同 curl 错误，但其所依赖的 32 个包最终下载成功（随后被 `#8` 的失败触发取消）。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了一个标准格式的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法和包名均正确。构建失败是由于 CI 构建时 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 连接不稳定所致，属于基础设施层面的暂时性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发重新构建即可。** 此类仓库镜像临时性 HTTP/2 流错误通常是短暂的基础设施波动（镜像服务器负载、网络抖动等），不是 PR 代码问题。建议在仓库镜像恢复稳定后重新触发 CI 构建。

## 需要进一步确认的点
- 如果多次重试 CI 仍然失败，需要排查 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 是否存在持续性的 HTTP/2 配置问题或服务器端故障。
- `#7`（stage-1）和 `#8`（builder）两个阶段都出现了相同的 curl error (92)，表明这不是单一连接的偶发问题，建议确认 CI runner 与仓库镜像之间的网络链路健康状况。
