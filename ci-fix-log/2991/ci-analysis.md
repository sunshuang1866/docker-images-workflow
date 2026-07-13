# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Stream error, No more mirrors to try, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: 在 aarch64 架构上，`dnf install` 从 `repo.openeuler.org` 的 `openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），其中 `guile` 包重试耗尽所有镜像后安装失败。这是 openEuler 24.03-LTS-SP4 aarch64 RPM 仓库的服务器端 HTTP/2 协议问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及其元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容与已有的 SP3 版本结构完全一致，仅将基础镜像和仓库源从 SP3 更换为 SP4。失败发生在 Docker 构建的第一步 `dnf install`，根本原因是 openEuler 24.03-LTS-SP4 的 aarch64 RPM 仓库存在 HTTP/2 服务端问题，与 PR 代码变更**无关**。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复后重试**。这是 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库的服务器端 HTTP/2 问题，多个 RPM 包下载出现 `INTERNAL_ERROR (err 2)`。观察日志中 `git-core` 包第一次失败后重试成功（1513.9 行），说明问题是**间歇性**的。建议在仓库服务器稳定后重新触发 CI 构建。

### 方向 2（置信度: 低）
**在 Dockerfile 中配置 DNF 重试参数**。如果此类 HTTP/2 错误在该仓库频繁出现，可在 Dockerfile 的 `dnf install` 命令中添加重试参数（如 `--setopt=retries=10`），提高对间歇性网络错误的容忍度。但这只能缓解症状，不能解决根本的服务端问题。

## 需要进一步确认的点
1. 该 `repo.openeuler.org` 的 SP4 aarch64 仓库 HTTP/2 问题是否为已知的持续性问题，还是单次构建的临时波动。
2. x86-64 架构的同一 PR 是否也遇到类似的 RPM 下载问题（当前仅提供了 aarch64 日志）。
3. SP3 仓库在同期是否也存在类似的 HTTP/2 问题——如果 SP3 正常而仅 SP4 异常，则 SP4 仓库本身可能存在配置或负载问题。

## 修复验证要求
无需验证。此问题属于 CI 基础设施故障，code-fixer 无需提交代码修改。如方向 2 被采纳（添加 DNF 重试），则 code-fixer 应在提交前确认该 `--setopt` 参数在 DNF 4.16（openEuler SP4 默认 DNF 版本）中可用。
