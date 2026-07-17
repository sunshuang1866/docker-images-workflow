# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `dnf install` 命令）
- 失败原因: CI 构建节点从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），最终 `gcc` 包在所有镜像站均重试失败，导致 DNF 安装命令以退出码 1 失败，整个 builder 阶段构建中止。同时运行的最终镜像阶段（#7）也随之被 CANCELED。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 仅新增了一个符合现有规范的 Dockerfile（使用与 SP3 版本相同的构建模式）以及配套的 meta.yml、image-info.yml、README.md 更新，不涉及任何语法或逻辑错误。错误完全发生在 `dnf install` 从上游 openEuler 仓库下载 RPM 包的阶段，属于 CI 基础设施/仓库镜像站的网络问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。Curl error (92) 是 HTTP/2 协议层面的服务端内部错误（`INTERNAL_ERROR`），通常由仓库镜像站的 HTTP/2 连接管理缺陷或中间代理/负载均衡器问题引起，属于 transient 故障。日志中阶段 #7 的 glibc-devel 和 gcc-gfortran 包在遭遇同样 HTTP/2 错误后通过自动重试成功下载，进一步佐证该问题为间歇性网络故障。多数情况下直接重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
**若该仓库持续出现 HTTP/2 流错误，且非 transient**，可在 Dockerfile 的 `dnf install` 前禁用 HTTP/2：
```
echo "http2=false" >> /etc/dnf/dnf.conf
```
使 dnf 通过 HTTP/1.1 下载，规避 HTTP/2 流中断问题。但此仅为规避方案，不应作为常规修复手段，且需要确认 openEuler 仓库服务器支持 HTTP/1.1 回退。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像站是否在同期其他 PR 的构建中也出现类似 HTTP/2 错误（判断是 transient 还是系统性故障）
- CI 构建节点（`ecs-build-docker-x86-03-sp`）的网络环境是否有 HTTP/2 代理或中间设备导致流中断
- 同样的 Dockerfile 在 aarch64 架构上的构建结果如何（本次日志仅为 x86-64，PR 声明了 amd64 + arm64 双架构支持）
