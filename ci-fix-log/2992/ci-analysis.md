# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `dnf install` 步骤）
- 失败原因: 构建过程中 openEuler 24.03-LTS-SP4 的软件仓库镜像（`repo.****.org`）出现 HTTP/2 协议传输错误（Curl error 92），导致 `gcc`、`gcc-gfortran`、`guile` 等多个 RPM 包下载失败。`dnf` 在尝试所有镜像源后仍无法成功下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`，构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次失败是 openEuler 24.03-LTS-SP4 软件仓库镜像的网络/协议层基础设施问题。PR 仅新增了多架构支持的 Dockerfile、更新了 README 和元数据文件，Dockerfile 中的 `dnf install` 命令语法正确、包名有效。同类错误也同时发生在另一个构建阶段（`#7` 即 stage-1 的 `dnf install`）中，但该阶段通过重试最终恢复，而 builder 阶段（`#8`）的 `gcc` 包重试耗尽所有 mirror 后失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，等待仓库恢复后重试。** 失败原因为 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 传输不稳定（Curl error 92），属于 CI 基础设施问题。Code Fixer 无需处理，建议：
- 等待仓库镜像恢复后重新触发 CI（`recheck` / `retest`）
- 如持续失败，联系 openEuler 仓库镜像运维团队排查 `repo.****.org` 的 HTTP/2 配置

### 方向 2（置信度: 低）
如果仓库镜像短期内无法修复，可考虑在 Dockerfile 的 `dnf install` 前添加重试或镜像源切换逻辑。但这属于绕过措施而非根治，不推荐作为首选方案。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像）在 CI 构建时间段（2026-07-09 14:46 UTC）是否存在已知网络故障或维护
- 确认同一时间段其他 PR 的 24.03-lts-sp4 相关构建是否也出现了同类错误（以判断是否为仓库侧的普遍性问题）

## 修复验证要求
无。此失败为 infra-error，不需要对代码做任何修改。
