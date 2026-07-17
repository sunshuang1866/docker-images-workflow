# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 仓库 HTTP/2 协议错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try, dnf install

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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder stage）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）返回 HTTP/2 协议层错误（`INTERNAL_ERROR (err 2)`），导致多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 等）反复下载失败，dnf 耗尽所有镜像重试后构建中断。`#7`（stage-1，即最终镜像阶段）也被级联取消。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次失败属于 CI 基础设施问题：openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在构建期间存在 HTTP/2 协议层缺陷，导致 libcurl 以错误码 92（`CURLE_HTTP2_STREAM`）中断下载。PR 仅新增了一个标准 Dockerfile（安装常规软件包）和配套元数据/文档更新，代码变更本身无误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败是 RPM 仓库镜像的临时性 HTTP/2 协议故障，与 PR 代码无关。等待仓库镜像恢复后重新触发 CI 构建即可。无需任何代码修改。

### 方向 2（置信度: 低）
若该仓库镜像持续不可用，可考虑在 Dockerfile 的 `dnf install` 前添加 repo 配置切换至备用镜像源（如 Huawei Cloud 镜像站），但这属于 CI 环境层面的 workaround，不应作为常规修复手段。

## 需要进一步确认的点
- 确认同一时间段内，其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也遭遇相同的 RPM 下载失败，以验证是否为仓库镜像的全局性故障。
- 确认 aarch64 架构 runner 上是否也出现相同错误（日志中仅包含 x86-64 runner 的输出）。
