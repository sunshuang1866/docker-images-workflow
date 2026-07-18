# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, rpm, mirror, MIRROR

## 根因分析

### 直接错误
```
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤的 `builder` 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在 CI 构建期间出现 HTTP/2 传输层错误（Curl error 92: INTERNAL_ERROR），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败，gcc 包在所有镜像重试后最终耗尽，导致 dnf install 退出码为 1，多阶段 Docker 构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 内容（构建命令、依赖包列表、sed 修改 Makefile 等）语法正确、逻辑合理。失败纯粹是因为 CI 构建环境在从 `repo.****.org/openEuler-24.03-LTS-SP4` 仓库下载 RPM 包时遭遇 HTTP/2 协议层传输错误（`INTERNAL_ERROR (err 2)`），属于基础设施/网络层面的问题。日志中 `#7`（stage-1）和 `#8`（builder）两个阶段均出现相同类型的 Curl error (92)，说明这不是单次偶然故障，而是仓库镜像侧存在持续的 HTTP/2 服务不稳定性。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 infra-error：openEuler 24.03-LTS-SP4 软件仓库的镜像节点 HTTP/2 服务不稳定。建议直接重新触发 CI 构建（retry），等待仓库镜像恢复稳定后构建即可通过。如果多次重试均失败，则需联系仓库镜像维护方排查 HTTP/2 协议栈问题。

### 方向 2（置信度: 低）
如果重试始终失败且无法等待仓库修复，可在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager --setopt max_parallel_downloads=1` 降低并发连接数或修改 dnf 配置强制使用 HTTP/1.1（`echo "http2=false" >> /etc/dnf/dnf.conf`），以绕过 HTTP/2 协议层的问题。但这仅为临时绕过手段，根本原因仍在仓库侧。

## 需要进一步确认的点
- 确认 `repo.****.org`（被屏蔽的仓库地址）在 CI 构建期间是否存在已知的 HTTP/2 服务中断或维护事件。
- 确认该仓库对 openEuler 24.03-LTS-SP4 源是否为新上线仓库，可能存在 HTTP/2 配置不完善的问题。
- 对比同一 CI 环境中其他 openEuler 版本（如 24.03-lts-sp3）的 `dnf install` 是否也受此影响——如果仅 SP4 源受影响，则可能是 SP4 仓库节点特有配置问题。
