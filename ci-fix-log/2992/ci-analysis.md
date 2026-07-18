# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `No more mirrors to try`, `dnf install`

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

多阶段构建中的 builder 阶段（#8）和 stage-1 运行时阶段（#7）均遭遇了多次 HTTP/2 流错误：

- `gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm`: 分别在 stream 31、37、15 上出现 Curl error (92)
- `glibc-devel-2.38-107.oe2403sp4.x86_64.rpm`: stream 17 出现 Curl error (92)
- `guile-2.2.7-6.oe2403sp4.x86_64.rpm`: stream 43 出现 Curl error (92)
- `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`: stream 27 出现 Curl error (92)，且所有镜像均重试失败

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库镜像在构建期间出现 HTTP/2 协议层故障（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个关键 RPM 包下载被中断，`dnf` 在尝试所有可用镜像后仍无法成功下载，构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个结构正确的 multiwfn Dockerfile（多阶段构建，以 `openeuler:24.03-lts-sp4` 为基础镜像）及配套的 README 和 meta 元数据文件更新。Dockerfile 中 `dnf install` 的包列表语法正确、包名合法。失败纯粹由 openEuler 24.03-LTS-SP4 软件仓库在构建时间窗口内的 HTTP/2 服务端故障引起。

## 修复方向

### 方向 1（置信度: 高）
**无需修改任何代码。** 这是 CI 基础设施的临时性网络问题（镜像源 HTTP/2 流不稳定），不是 PR 引入的代码缺陷。建议在 openEuler 镜像源恢复稳定后，重新触发 CI 运行（retry）即可通过。

## 需要进一步确认的点
- 若多次重试后仍持续失败，需排查 openEuler 24.03-LTS-SP4 仓库 CDN/镜像节点的 HTTP/2 服务健康状况。
- 确认 CI runner 所在网络环境到 `repo.****.org` 的 HTTP/2 连接是否持续存在协议层异常。
