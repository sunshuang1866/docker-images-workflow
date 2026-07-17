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
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库服务器在 CI 构建期间出现 HTTP/2 协议层错误（`INTERNAL_ERROR`），导致多个包（`gcc-gfortran`、`guile`、`gcc`）下载失败。`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像均尝试失败后，dnf 报错退出。该问题同时影响了 builder 阶段（stage #8）和 stage-1 阶段（stage #7 也出现了同类 `[MIRROR]` 下载错误，如 `glibc-devel` 和 `gcc-gfortran`，但在 builder 失败后被 CANCELED）。

### 与 PR 变更的关联
PR 变更与此次失败**无关**。PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正常，所列包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。失败是由 CI 基础设施侧的网络问题（openEuler RPM 镜像站的 HTTP/2 连接异常）导致，属于临时性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
这是一个 **CI 基础设施问题**，与 PR 代码无关，无需修改任何文件。建议重新触发 CI 构建（retry），待 openEuler 24.03-LTS-SP4 仓库镜像站恢复后构建即可通过。

### 方向 2（置信度: 中）
如果多次重试均失败，可考虑在 Dockerfile 中的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 以禁用 HTTP/2，回退到 HTTP/1.1，绕过 HTTP/2 协议层瞬时错误。但这是临时 workaround，不应作为永久方案。

## 需要进一步确认的点
- 检查 openEuler 24.03-LTS-SP4 仓库镜像站（repo.****.org）在构建时段的可用性状态，确认是否为临时故障。
- 确认同类 openEuler 24.03-LTS-SP4 的其他镜像构建 job 是否也出现了相同的 HTTP/2 错误，以排除本 PR 构建节点的个别网络问题。
