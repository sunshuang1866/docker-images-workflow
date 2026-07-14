# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing, INTERNAL_ERROR, MIRROR, No more mirrors to try, dnf, repo

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
- 失败位置: Dockerfile:7-10（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 HTTP/2 层频繁出现流错误（`Stream error ... INTERNAL_ERROR (err 2)`），dnf 在逐一尝试所有可用 mirror 后仍无法下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（以及其他多个包如 `gcc-gfortran`、`glibc-devel`、`guile`），最终包下载失败导致 docker build 退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅添加了一个新的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）和配套的元数据文件（README.md、image-info.yml、meta.yml）。失败原因是 openEuler 24.03-LTS-SP4 的 RPM 仓库在 CI 构建时段出现 HTTP/2 连接稳定性问题。日志中两个阶段（builder #8 和 final #7）均从同一仓库下载时遇到相同的 `Curl error (92)` 错误，证明这是仓库端的网络/协议问题，与 Dockerfile 内容（安装的包列表、编译命令等）无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个 CI 基础设施问题，应由 CI 运维团队检查 `repo.****.org` 上 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务状态。可能的原因包括：
- 仓库所在 CDN/镜像节点的 HTTP/2 配置不稳定
- 网络链路质量问题导致 HTTP/2 stream 频繁被非正常关闭
- 仓库服务端存在临时的负载或协议层 bug

建议 CI 运维重试构建任务，或暂时降级 curl/dnf 使用 HTTP/1.1（如通过 `--setopt=minrate=0` 或调整 DNF 的 `ip_resolve` 和 `http2` 相关配置）。

## 需要进一步确认的点
- 确认 `repo.****.org` 在构建时段（2026-07-09 14:46~14:55 UTC）是否存在已知的 HTTP/2 服务异常或 CDN 节点故障。
- 确认同期其他使用 openEuler 24.03-LTS-SP4 base image 的 PR 是否也遇到相同的 dnf 下载失败（可交叉验证是否为此仓库的系统性问题）。
- 重试该 CI 任务，观察问题是否仍然复现；若不再复现，则可确认是临时性网络波动。
