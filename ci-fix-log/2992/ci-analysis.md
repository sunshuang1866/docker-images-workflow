# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 HTTP/2 连接层频繁出现 `INTERNAL_ERROR` 流错误，导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个大型包下载反复失败，最终 `gcc-12.3.1` 耗尽了所有镜像重试次数仍无法下载成功。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`、README 更新、image-info.yml 和 meta.yml 条目，均为纯声明性/文档性变更。失败的直接原因是 openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像在构建期间存在 HTTP/2 协议层的不稳定性（Curl error 92），这属于外部基础设施问题，任何使用该仓库的构建作业均会受影响。Dockerfile 中 `dnf install` 的包列表和命令本身与已有 SP3 版本一致，不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**等待并重试。** 此为 openEuler 24.03-LTS-SP4 RPM 仓库镜像的临时性 HTTP/2 连接故障，与 PR 代码无关。建议等待仓库镜像恢复后重新触发 CI 构建。若问题持续存在，可联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务器配置。

### 方向 2（置信度: 低）
若仓库镜像问题无法在短期内解决，可考虑在 Dockerfile 的 `dnf install` 前添加重试逻辑（如 `dnf install -y --setopt=retries=10 ...`）或将 `dnf` 强制降级为 HTTP/1.1 连接（设置 `ip_resolve=4` 或通过 `echo "http/1.1"` 相关配置），但这些均为绕过方案而非根因修复。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在近期是否存在已知的 HTTP/2 服务问题或维护计划
- 同一时间段内其他依赖 openEuler 24.03-LTS-SP4 仓库的 CI 构建是否也出现类似失败（以确认问题范围）
- 仓库镜像是否支持 HTTP/1.1 回退连接
