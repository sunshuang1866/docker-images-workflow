# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:7-10（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在构建期间持续返回 HTTP/2 流错误（curl error 92: `INTERNAL_ERROR`），导致多个 RPM 包（gcc-gfortran、guile、gcc）下载失败。最终 gcc 包（34 MB）耗尽所有镜像重试次数，`dnf install` 以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 的变更内容为：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（标准的多阶段 Dockerfile，与已有的 sp3 版本模式一致）
2. 更新 `README.md`、`image-info.yml`、`meta.yml` 以注册新镜像

这些变更均为常规的"添加新 OS 版本支持"操作，Dockerfile 语法和依赖声明本身没有问题。失败完全发生在 `dnf install` 从 openEuler 官方仓库下载 RPM 包的网络阶段，属于 CI 基础设施侧（仓库镜像服务）的瞬态故障，与 Dockerfile 内容和代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端瞬态故障，与 PR 代码无关。等待仓库服务恢复后重新触发 CI 流水线即可。无需修改任何代码或 Dockerfile。

## 需要进一步确认的点
- 如果多次重试后仍然失败，需确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）的 HTTP/2 服务是否存在持续性故障，可联系仓库运维团队排查。
- 日志中 `#7`（stage-1 阶段）也在下载 gcc-gfortran 时遇到同类 HTTP/2 错误（`#7 1598.9 [MIRROR] gcc-gfortran-...: Curl error (92)`），但通过重试正在恢复中，最终因 `#8` 失败而被 `CANCELED`。这进一步说明网络问题影响范围是全局性的，而非特定包的发布缺失。
