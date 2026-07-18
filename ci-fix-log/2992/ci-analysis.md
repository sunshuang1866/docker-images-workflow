# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2协议故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, INTERNAL_ERROR, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库（`repo.****.org`）的 HTTP/2 协议层面出现间歇性故障，`curl` 下载 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个 RPM 包时反复报 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，`dnf` 在耗尽所有镜像重试后放弃并返回 exit code 1。两个 Docker 构建阶段（#7 stage-1 和 #8 builder）均受波及。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个合法的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容（`dnf install` 包列表、`git clone`、`sed` + `make` 编译）语法和逻辑均正确。失败完全由 openEuler 镜像仓库的 HTTP/2 协议层故障引起，属 CI 基础设施问题。证据：日志中 stage-1（#7，运行不同包列表的 `dnf install`）也出现了完全相同的 `Curl error (92)` 错误，说明问题在仓库端而非 Dockerfile 内容。

## 修复方向

### 方向 1（置信度: 低）
**无需代码修改。** 这是临时的基础设施网络故障，等待 openEuler 镜像仓库恢复后重跑 CI 即可。Code Fixer 无需处理。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 官方 RPM 仓库（`repo.****.org`）在 CI 运行时段（2026-07-09 14:46-14:48）是否存在已知的 HTTP/2 服务中断或降级。
- 若该仓库持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo 'http2=false' >> /etc/dnf/dnf.conf` 或 `dnf install -y --setopt=retries=10` 作为网络波动的缓解措施，但这属于可选优化而非本次 CI 失败的必要修复。
