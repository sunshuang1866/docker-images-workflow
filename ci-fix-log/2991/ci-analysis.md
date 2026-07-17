# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2连接中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 软件仓库出现间歇性 HTTP/2 流错误（Curl error 92），多个 RPM 包（`git-core`、`gcc-c++`、`guile`）在下载过程中遭遇 `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR (err 2)`。其中 `git-core` 和 `gcc-c++` 在重试后成功下载，但 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在重试耗尽后下载失败，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。本次 PR 新增了一个标准结构的 Dockerfile（安装编译工具 → 克隆源码 → cmake 构建），Dockerfile 内容本身正确且语法无误。失败发生在 `dnf install` 从官方仓库下载 RPM 包的阶段，属于 openEuler 软件仓库 `repo.openeuler.org` 的临时性 HTTP/2 基础设施问题。PR 未修改任何现有文件，仅新增了 4 个文件，不会触发此错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 即可。** 该失败是 openEuler 官方软件仓库 `repo.openeuler.org` 的临时性 HTTP/2 连接异常，与 Dockerfile 内容或 PR 变更无关。等待仓库服务恢复后重新触发 CI 构建，或联系 openEuler 基础设施团队确认仓库服务状态。

### 方向 2（置信度: 中）
如果重试后仍持续失败，可在 Dockerfile 的 `dnf install` 前添加 `dnf install` 的重试机制（如利用 dnf 的 `--setopt=retries=10` 参数增加下载重试次数），或考虑在构建环境配置中切换到备选镜像站（如 `repo.huaweicloud.com`）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当前时段的 aarch64 架构 openEuler 24.03-LTS-SP4 仓库服务状态是否正常。
- 确认该失败是否在 x86_64 架构构建中复现（当前日志仅覆盖 aarch64 构建）。若 x86_64 也失败且报相同的 HTTP/2 错误，则进一步确认是仓库端问题而非特定架构节点问题。
- 检查是否同一时段有其他 openEuler 24.03-LTS-SP4 的 PR 构建遇到相同 Curl error (92)，以验证是否为仓库端普遍性问题。
