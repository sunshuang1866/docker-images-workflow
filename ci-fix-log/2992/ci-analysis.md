# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器在处理 HTTP/2 请求时频繁返回内部流错误（`Curl error (92)`），导致 `dnf` 在尝试所有镜像后仍然无法下载 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包，最终构建失败。这是一个**CI 基础设施/上游仓库服务端问题**，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** 本次 PR 仅做了以下纯文档/元数据变更：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（新镜像的 Dockerfile）
- 在 `README.md`、`image-info.yml`、`meta.yml` 中添加对应的镜像条目

失败发生在 Dockerfile 构建阶段的 `dnf install` 步骤，且两个并行的构建阶段（builder 阶段 `#8` 和 runtime 阶段 `#7`）同时出现了相同的 HTTP/2 流错误，说明问题是 openEuler 24.03-LTS-SP4 仓库服务端的普遍性问题，而非 Dockerfile 内容（如包名拼写错误、依赖冲突等）导致。日志中可以看到其他使用 openEuler 24.03-lts-sp3 的预检步骤（通过 dnf 安装 `python3-dnf`、`git`、`python3-pip` 等）**均正常完成**，进一步佐证 `sp4` 仓库在 CI 运行时刻存在网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复，重试即可。** 该失败为 openEuler 24.03-LTS-SP4 仓库镜像的**临时性网络/服务端问题**，与 PR 代码无关。Code Fixer 无需对任何文件做出修改。建议在仓库服务恢复后重新触发 CI 构建。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 运行时间段是否存在已知的服务中断或维护事件。
2. 重新触发一次 CI 构建后，相同错误是否仍然复现。若持续复现，则需要排查 CI runner 与 openEuler 24.03-LTS-SP4 仓库之间的网络连通性，或考虑为 Dockerfile 添加 `dnf install` 的 `--retries` 参数以提高网络容错能力（但此优化不属于本次修复范围）。
