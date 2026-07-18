# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP2流错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR (err 2)`, `dnf install`, `No more mirrors to try`

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 步骤）
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.*.org`）持续返回 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer, INTERNAL_ERROR`），导致 `gcc`（34MB）等多个大型 RPM 包下载失败，最终 dnf 重试所有镜像后放弃下载。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了多路并行构建（multi-stage）下的 Dockerfile 及配套元数据文件，Dockerfile 中的 `dnf install` 命令语法和包名均正确无语法错误。失败根因是 SP4 仓库镜像服务器的 HTTP/2 协议栈存在问题，导致 TCP 流异常关闭（`INTERNAL_ERROR`），与 PR 的 Dockerfile 内容或构建逻辑无关。两个并行构建阶段（`#7` 和 `#8`）均受到不同程度的影响——`#7` 阶段（runtime，32 个包）在 `gcc-gfortran` 和 `glibc-devel` 上遭遇 MIRROR 错误后尝试恢复中；`#8` 阶段（builder，157 个包）在 `gcc` 包上连续失败三次后耗尽所有镜像。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该错误为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层瞬态故障（`INTERNAL_ERROR` on stream close），与 Dockerfile 内容无关。此类网络层错误通常在仓库服务恢复后重试即可通过。建议直接 retry 该 PR 的 CI job。

### 方向 2（置信度: 低）
若多次重试仍失败，可能是 `repo.*.org` 的 CDN/镜像节点对 HTTP/2 长连接支持不稳定。可在 Dockerfile 的 `dnf install` 前添加 `echo "http2=0" >> /etc/dnf/dnf.conf` 或 `echo "max_parallel_downloads=3" >> /etc/dnf/dnf.conf`，降低并发连接数以缓解 HTTP/2 流错误，但这是绕过方案而非根本解决。

## 需要进一步确认的点
1. 确认该 SP4 仓库镜像（`repo.*.org`）当前是否从其他 PR 构建也出现同类 HTTP/2 错误，以排除是广义的镜像服务故障。
2. 若仅该 PR 持续失败而其他使用 SP4 的 PR 正常，需检查 CI runner 节点 `ecs-build-docker-x86-03-sp` 到 `repo.*.org` 的网络链路质量。
3. 确认 SP3（`24.03-lts-sp3`）的同一镜像仓库在同时期是否也有类似 HTTP/2 错误，以判断问题是否仅限 SP4 仓库。
