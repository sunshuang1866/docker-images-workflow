# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], No more mirrors to try, dnf install, INTERNAL_ERROR (err 2)

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境中访问 openEuler 24.03-LTS-SP4 官方 RPM 仓库时，多个 HTTP/2 流发生 `INTERNAL_ERROR (err 2)` 协议错误，`gcc-c++` 包（13 MB）在两次 stream 失败后所有镜像均已重试耗尽，导致 `dnf install` 失败。`cmake-data` 和 `git-core` 虽也遇到同类错误，但通过镜像重试机制最终成功下载（说明这是间歇性网络问题而非仓库侧永久故障）。

### 与 PR 变更的关联

**无关。** PR 变更内容为新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、doc/image-info.yml、meta.yml），Dockerfile 语法正确、dnf 包名列表合法。失败根因为 openEuler 24.03-LTS-SP4 官方 RPM 仓库在 CI 构建时段出现 HTTP/2 协议层面的间歇性流错误（Curl error 92），属于 CI 基础设施网络故障，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库镜像恢复后重试 CI**。该错误为 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 协议故障，`cmake-data` 和 `git-core` 均已通过镜像自动重试成功下载，表明问题具有间歇性。可等待仓库侧恢复后重新触发 CI 流水线。

### 方向 2（置信度: 中）
**在 Dockerfile 中为 dnf 添加重试参数以提高鲁棒性**。在 `dnf install` 命令中添加 `--setopt=retries=10` 等重试配置，增加对间歇性网络故障的容忍度。但此方法无法从根本上解决 HTTP/2 协议层面的镜像仓库问题。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在此构建时段是否存在已知的 HTTP/2 服务问题或维护事件。
- 确认是否只有 x86_64 架构的构建节点受影响，还是 aarch64 节点也同样失败（日志仅包含 x86-64 runner）。
- 确认同类 SP4 基础镜像的其他 PR 构建是否在同时间段出现相同 `Curl error (92)` 错误，以排除 runner 节点本地网络问题。

## 修复验证要求
无需修复验证。此失败为 infra-error，与代码变更无关。
