# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 ... INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 ... INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境（Jenkins node `ecs-build-docker-x86-03-sp`）在通过 `dnf` 从 openEuler 24.03-LTS-SP4 官方镜像仓库下载 RPM 包时，遭遇 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）的 HTTP/2 流被服务端异常关闭（`INTERNAL_ERROR (err 2)`），经过多次重试后，`gcc-12.3.1-110.oe2403sp4.x86_64` 耗尽所有镜像源，`dnf install` 失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了以下文件/条目：
- `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（新增 47 行的新架构变体）
- `Others/multiwfn/README.md`（新增 2 行表格条目）
- `Others/multiwfn/doc/image-info.yml`（新增 1 行条目）
- `Others/multiwfn/meta.yml`（新增 2 行条目）

Dockerfile 内容语法正确，`dnf install` 的包名均有效（`#7` 阶段在相同镜像仓库上成功解析了依赖并开始下载部分包）。失败原因是 **openEuler 镜像仓库服务器的 HTTP/2 协议实现异常**，属于 CI 基础设施/Mirror 侧问题，与本次 PR 的代码变更无关。

值得注意的是，`#7`（stage-1 运行时阶段）在同步下载过程中也遭遇了同样的 HTTP/2 stream 错误（`glibc-devel`、`gcc-gfortran`），但因重试机制最终成功下载了其中部分包，最终因 `#8` 彻底失败而被 `CANCELED`。这两个独立构建阶段的并发下载均复现了 HTTP/2 协议错误，进一步佐证这是镜像站侧的系统性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复。** 这是一个 CI 基础设施 / openEuler 镜像仓库网络的瞬时故障。应执行以下操作之一：
- 在 Jenkins 上重新触发该 job 的构建（retry）
- 如问题持续复现，联系 openEuler 镜像仓库运维团队排查 HTTP/2 服务端配置

### 方向 2（置信度: 低）
如果该问题频繁发生在特定镜像仓库上，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 配置降低 HTTP 协议版本（如强制 HTTP/1.1），或更换镜像源。但鉴于当前是一次性传输层错误，不推荐为此修改 Dockerfile。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 镜像仓库在同一时间段是否对其它 PR 的构建也产生了类似的 HTTP/2 stream 错误（确认是否为集群性问题）
- 重试构建后是否通过（验证是否为瞬时网络故障）
