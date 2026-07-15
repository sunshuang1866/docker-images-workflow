# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: 构建过程中，openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输层反复出现 `INTERNAL_ERROR (err 2)` 流错误。多个 RPM 包（`gcc-gfortran`、`guile`、`gcc`）的下载均受波及，虽然 `gcc-gfortran` 和 `guile` 经重试后成功下载，但 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB）在所有镜像均被尝试后仍下载失败，导致 `dnf install` 退出码为 1，Docker 构建终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文档更新（README.md、image-info.yml、meta.yml）。Dockerfile 中 `dnf install` 命令语法正确，安装的包（`git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`）均为 openEuler SP4 官方仓库中明确存在的基础包。失败完全由 CI 构建环境与 openEuler SP4 仓库镜像之间的 HTTP/2 网络协议问题导致。

日志中也可见 stage-1（#7 运行阶段）的 `dnf install` 同样遭遇了 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），但通过重试幸免于难，进一步证明这是系统性的网络基础设施问题，而非 Dockerfile 编写错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 构建即可。** 失败原因是 openEuler SP4 仓库镜像的 HTTP/2 传输层在构建时不稳定，属于临时性基础设施问题。在镜像仓库服务恢复稳定后重新触发 CI 构建，大概率能直接通过。

### 方向 2（置信度: 低，仅当方向1持续失败时考虑）
如果多次重试后仍失败，可能是 CI 构建节点的网络环境与 openEuler SP4 仓库的 HTTP/2 实现存在持续兼容性问题。可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 或 `sed` 操作，将仓库访问协议从 HTTP/2 降级为 HTTP/1.1（通过 curl 的 `--http1.1` 或 dnf 的 `http2=false` 配置）。但此方向**不应**在首次诊断时实施，应先确认 infrastructure 已恢复。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在构建时段是否存在已知服务降级或 HTTP/2 协议问题。
2. 确认 CI 构建节点（`ecs-build-docker-x86-03-sp`）到该仓库的网络链路是否稳定。
3. 观察同一时段其他 openEuler SP4 镜像（如 `oneapi-basekit`、`oneapi-runtime` 等已存在的 SP4 镜像）的 CI 构建是否也出现了类似的 RPM 下载失败，以确认是否为仓库侧系统性问题。
