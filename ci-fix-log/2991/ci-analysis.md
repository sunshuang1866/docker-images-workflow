# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包的 HTTP/2 传输流异常中断（Curl error 92: INTERNAL_ERROR）。其中 `git-core` 和 `gcc-c++` 经重试后成功下载，但 `guile`（git 的传递依赖）在重试耗尽所有 mirror 后仍未成功，导致 `dnf install` 以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 这是一个纯粹的 CI 基础设施问题。Dockerfile 中 `dnf install` 命令本身完全正确——所请求的包（git、gcc、gcc-c++、make、cmake）均是 openEuler 24.03-LTS-SP4 仓库中存在的标准包。失败原因是 `repo.openeuler.org` 的 aarch64 包仓库在 HTTP/2 层存在服务器端流传输错误，导致部分大型 RPM 包（如 `guile` 6.3MB）下载中断。

需要特别指出：**x86_64（amd64）架构的构建可能已成功**，当前日志仅来自 aarch64 runner 的构建过程。日志中 `#7` 步骤在下载阶段的三个包（`git-core`、`gcc-c++`、`guile`）均出现过 Curl error 92，说明 `repo.openeuler.org` 的 aarch64 仓库在此期间普遍不稳定。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 openEuler 官方 RPM 镜像仓库（`repo.openeuler.org`）的临时网络/服务端问题，应通过以下方式处理：

1. **等待仓库恢复后重试 CI**：`Curl error (92)`（HTTP/2 INTERNAL_ERROR）通常是服务端临时故障，重新触发 CI 构建（retry）大概率可以通过。
2. **如果持续失败，联系 openEuler 基础设施团队**：排查 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 配置，考虑是否有 CDN 节点或反向代理存在问题。

### 方向 2（置信度: 低，仅在方向 1 无效后考虑）
如果 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 问题长期不能修复，可在 Dockerfile 中将 `dnf install` 改为 `dnf install --setopt=retries=10`（增加下载重试次数），或通过在 base image 中预先安装关键构建依赖来规避此问题。但这只是绕过而非根因修复，不推荐作为首选方案。

## 需要进一步确认的点
1. 检查同一 CI run 中 **x86_64（amd64）架构**的 vvenc 构建是否成功（若 x86_64 也失败且报相同错误，则仓库问题更普遍；若成功，则仅 aarch64 仓库节点有问题）。
2. 确认 `repo.openeuler.org` 的服务状态——是否在 CI 构建时间窗口（2026-07-09 14:08 UTC）有已知的 aarch64 仓库故障或维护公告。
3. `guile` 包（6.3MB）是 git 的强依赖（`Requires: guile`），即使通过增加 retries 使其下载成功，其他大型包（如 `gcc` 30MB、`cmake` 13MB）也存在同样的 HTTP/2 中断风险。

## 修复验证要求
不适用——本失败为 infra-error，无需修改任何代码文件。若后续重试 CI 仍失败，code-fixer 应首先确认失败是否仍然为相同的 Curl error (92)，而非新的错误类型。
