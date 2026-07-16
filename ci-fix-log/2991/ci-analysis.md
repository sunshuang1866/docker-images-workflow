# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 aarch64 仓库的 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92），其中 `git-core`、`gcc-c++` 在重试后成功下载，但 `guile`（git 的传递依赖）耗尽所有镜像重试次数后仍失败，导致整个 `dnf install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 命令本身无问题。失败原因是 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时存在 HTTP/2 传输层间歇性故障。日志中同时出现了 `git-core` 和 `gcc-c++` 的同类型 Curl 错误（92），说明这是仓库侧的普遍网络问题，而非特定包的损坏。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该错误为仓库侧 HTTP/2 流传输的间歇性故障，属于基础设施问题。`git-core` 和 `gcc-c++` 在重试后均成功下载，表明问题具有瞬时性。直接重试 CI 大概率可以成功。

### 方向 2（置信度: 低）
**为 dnf 增加重试/超时参数**。若重试后仍频繁出现同类错误，可在 Dockerfile 的 `dnf install` 命令中添加重试和超时配置（如 `--setopt=retries=10 --setopt=timeout=120`），增强对网络波动的容忍度。但此方向仅为防御性措施，不能解决仓库侧的根本问题。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 aarch64 仓库的 HTTP/2 流错误是否为长期性问题（可通过多次重试 CI 来验证）
- 同一 PR 的 x86_64 构建是否也失败（日志中仅包含 aarch64 runner 的输出，若 x86_64 也失败且错误表现不同，则可能存在其他问题）
