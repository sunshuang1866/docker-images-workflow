# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: 构建过程中，openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站出现 HTTP/2 协议层流错误（Curl error 92），多个软件包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。gcc 包（34 MB）在尝试了所有可用镜像后均未成功，`dnf` 最终报错退出。这是 CI 基础设施/仓库镜像站的网络问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile（以及对应的 README、image-info.yml、meta.yml 条目），该 Dockerfile 中的 `dnf install` 步骤语法和包名均正确无误。失败原因是构建时 openEuler 24.03-LTS-SP4 的官方 RPM 仓库镜像站出现了 HTTP/2 协议层通信错误，导致大体积包（gcc 34 MB）在多次重试后仍无法下载完成。同样的问题也影响了 `#7`（stage-1 运行时阶段）的 `dnf install`，只是该阶段在 `#8` builder 阶段失败后被 CANCELED。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是 CI 基础设施问题，正确做法是等待仓库镜像站恢复稳定后重试构建（retry the CI job）。PR 新增的 Dockerfile、README、image-info.yml、meta.yml 均无语法或逻辑错误。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站（`repo.****.org`）在构建时间点（2026-07-09 14:46 UTC 前后）是否存在已知的 HTTP/2 协议问题或服务降级。
- 该镜像站的 HTTP/2 支持是否稳定——如果频繁出现此类 Curl error (92)，可建议 CI 构建环境强制使用 HTTP/1.1（如通过 `dnf` 配置 `http2=false` 或设置 `CURLOPT_HTTP_VERSION` 环境变量），但这属于 CI 基础设施层面的调整，不属于本次 PR 修复范围。
