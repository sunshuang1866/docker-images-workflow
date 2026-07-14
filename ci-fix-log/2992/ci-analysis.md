# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, openEuler repo, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.****.org`）在构建期间出现 HTTP/2 流层错误（`Curl error (92): INTERNAL_ERROR`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载失败，最终 `gcc` 包在所有镜像源上尝试后均告失败，dnf 退出码为 1。两个并行的构建阶段（`#7` stage-1 和 `#8` builder）均遭遇同类错误。

### 与 PR 变更的关联
**与 PR 改动无关。** 该 PR 仅新增了一个适用于 openEuler 24.03-LTS-SP4 的 Dockerfile，其 `dnf install` 命令语法正确，声明的包名（`git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`）均为 openEuler 仓库中真实存在的包。构建失败完全由 CI 构建时刻 openEuler 官方仓库的网络/服务端 HTTP/2 协议故障引起，属于偶发性基础设施问题。

此外，已经成功安装了同一组依赖的旧版 `24.03-lts-sp3` 构建在本次日志中未出现（日志显示仅构建了 sp4 的 Dockerfile），无法直接对比。但 sp3 的现有 Dockerfile 使用了相同的包列表且历史上构建成功（CI 之前已通过），这进一步佐证了 sp4 的失败是外部仓库问题而非 Dockerfile 错误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是 openEuler 24.03-LTS-SP4 仓库在特定时间窗口内出现的 HTTP/2 服务端故障，属于偶发性基础设施问题。Dockerfile 本身无语法或逻辑错误，无需修改代码。等待仓库恢复正常后重新触发 CI 流水线即可。

## 需要进一步确认的点
- 若多次重试后依然失败，需排查 openEuler 24.03-LTS-SP4 仓库是否存在持续的服务端问题，或该仓库是否对 CI 构建来源 IP 有访问限制（如速率限制）。
- 可尝试在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 并在 install 时加 `--setopt=retries=5` 参数，提升网络波动时的容错性（但此变更仅是优化，非修复根因，根因在仓库端）。
