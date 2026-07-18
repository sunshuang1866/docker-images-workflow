# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2镜像源流传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], No more mirrors to try

## 根因分析

### 直接错误

```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
------

ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（dnf install 步骤）
- 失败原因: CI 构建环境在通过 HTTP/2 协议从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（`gcc-gfortran`、`guile`、`gcc`、`glibc-devel`）遭遇 Curl error (92) HTTP/2 流帧层错误（`INTERNAL_ERROR`）。`dnf` 在尝试所有可用镜像源后仍无法成功下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`，最终安装失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（`dnf install` 安装编译依赖 → git clone → make 编译）和配套的元数据/文档文件。失败发生在 `dnf install` 阶段，这是一个纯网络/基础设施问题——openEuler 24.03-LTS-SP4 镜像仓库的 HTTP/2 服务端在某些流上异常终止连接。日志中 `#7`（stage-1 最终镜像层）和 `#8`（builder 层）**同时独立**出现 HTTP/2 流错误，进一步证明这是仓库侧的间歇性故障，而非 Dockerfile 或命令本身的错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施/镜像仓库的网络问题（HTTP/2 流中断），与 PR 代码变更无关。建议：
- 重新触发 CI 构建（retry），在网络状况正常时段重试即可通过。
- 如果该镜像仓库的 HTTP/2 故障持续出现，可考虑在 Dockerfile 中为 `dnf` 命令添加 `--retries` 和延长超时参数（如 `--setopt=timeout=300 --setopt=retries=10`）以提高抗网络波动的能力，但这属于增强性措施而非必需修复。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在构建时段是否存在 HTTP/2 服务端问题。
- 如该问题在多次重试后依然复现，需排查 CI Runner 的出站网络策略或代理配置是否干扰了 HTTP/2 长连接。
