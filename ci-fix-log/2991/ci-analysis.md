# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, dnf install, aarch64

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 的 aarch64 软件包仓库（`repo.openeuler.org`）在 CI 构建期间持续返回 HTTP/2 流内部错误（`INTERNAL_ERROR (err 2)`），导致多个 RPM 包（git-core、gcc-c++、guile）下载失败，dnf 耗尽所有镜像重试后终止安装过程。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 内容格式正确，`dnf install` 命令列出的包（git、gcc、gcc-c++、make、cmake）均为 openEuler 24.03-LTS-SP4 仓库中的标准包。构建失败的唯一原因是 openEuler 官方软件包仓库在 aarch64 架构上存在 HTTP/2 协议层面的服务端问题，属于 CI 基础设施故障。PR 改动本身没有引入任何代码错误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 openEuler 软件包仓库的临时性 HTTP/2 服务端故障，PR 代码无需任何修改。等待 `repo.openeuler.org` 的 aarch64 仓库恢复后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
若问题持续出现，可在 Dockerfile 中为 `dnf install` 添加 `--retries` 和 `--setopt=timeout=...` 参数来增强下载重试的鲁棒性，但这无法从根本上解决服务端 HTTP/2 协议错误。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库当前是否仍有 HTTP/2 问题（可尝试手动 `curl` 测试）
- 确认 x86_64 架构的同版本 vvenc 构建是否也遇到相同问题（当前日志仅为 aarch64 runner 的输出）
