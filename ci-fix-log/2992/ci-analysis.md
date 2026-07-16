# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, INTERNAL_ERROR

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（RUN dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输层存在持续性的流错误（Curl error 92: `INTERNAL_ERROR`），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败，gcc 包在所有镜像源尝试耗尽后最终失败，导致 `dnf install` 返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关。**

PR #2992 的改动仅为新增 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套的 README、image-info.yml、meta.yml 更新，属于标准的新 OS 变体支持。新增 Dockerfile 的 `dnf install` 命令语法正确、包名合法、遵循现有 sp3 变体的成熟模式。失败原因为 CI 运行时所连接的 openEuler 24.03-LTS-SP4 仓库镜像出现 HTTP/2 传输层故障，属于基础设施层面的临时性问题，PR 代码本身无任何错误。

值得注意的是，日志中 `#7`（stage-1 / 最终阶段）也触发了同样的 `Curl error (92)`（glibc-devel 和 gcc-gfortran 下载失败），但 `#7` 被标记为 `CANCELED` 而非 `FAILED`——因为 builder 阶段（`#8`）先一步耗尽所有重试后失败，导致整个构建流水线终止。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是一个基础设施层面的临时性网络故障（openEuler SP4 仓库镜像 HTTP/2 流错误）。PR 的 Dockerfile 代码本身正确无误。建议等待仓库镜像恢复稳定后，重新触发 CI 流水线。如果多次重试后仍然失败，则需联系 openEuler 基础设施团队排查 SP4 仓库镜像的 HTTP/2 服务端配置。

### 方向 2（置信度: 低）
如果该仓库镜像 HTTP/2 问题持续存在且短期无法修复，可在 Dockerfile 的 `dnf install` 前添加 curl 的 HTTP/2 降级配置（如设置 curl 回退到 HTTP/1.1），但这是规避手段而非根因修复，应由基础设施侧解决。

## 需要进一步确认的点
1. 是否存在其他 SP4 变体的 PR（即同样依赖 openEuler 24.03-LTS-SP4 仓库的 Dockerfile）也在近期 CI 中失败？如果是，可确认这是仓库基础设施的全局故障。
2. openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端近期是否有变更或维护操作？
3. 日志中仓库域名 `repo.****.org` 被脱敏，需要确认实际仓库地址，以排查是否该仓库对 CI 出口 IP 有速率限制或连接数限制。
