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
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的包仓库镜像 `repo.****.org` 在处理 HTTP/2 请求时返回协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`，具体为 `INTERNAL_ERROR (err 2)`），导致多个 RPM 包下载失败。`gcc` 包在重试完所有可用镜像后仍下载失败，`dnf install` 以 exit code 1 退出。`stage-1` 阶段的 `dnf install` 也受到相同影响（`glibc-devel`、`gcc-gfortran` 下载报同类错误），在 builder 阶段失败后被 CANCELED。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（47 行新文件）以及相应的 README、image-info.yml、meta.yml 文档更新。失败发生在 Dockerfile 构建过程中最基础的 `dnf install` 依赖安装步骤，该步骤从 openEuler 官方包仓库下载系统包，是仓库服务器端的 HTTP/2 协议层故障，与 Dockerfile 内容、PR 的任何代码变更均无关联。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复后重试。** 这是 openEuler 包仓库 `repo.****.org` 的 HTTP/2 服务端临时故障。Dockerfile 本身无需任何修改。建议在仓库服务恢复正常后重新触发 CI 构建。

### 方向 2（置信度: 低）
若该仓库镜像持续不可用，可考虑在 `dnf install` 前切换 openEuler 仓库镜像源（修改 `/etc/yum.repos.d/` 中的 repo 配置），将出问题的 `repo.****.org` 替换为其他可用镜像。但这应作为 CI 基础设施层面的全局配置变更，不应在单个 Dockerfile 中 hack。

## 需要进一步确认的点
- 确认 `repo.****.org` 是否已恢复正常服务（该镜像域名已被脱敏为 `****`，需运维确认实际域名及当前状态）。
- 确认该仓库镜像的 HTTP/2 协议层故障是否有已知的运维告警或计划维护。
- 若该故障持续频发，建议 CI 层面为 dnf 配置添加 `retries` 参数或切换到 HTTP/1.1 协议备用。

## 修复验证要求
无需代码修复。此为 infra-error，修复验证仅需确认仓库镜像服务恢复正常后重跑 CI 即可。
