# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包过程中遭遇多次 HTTP/2 流内部错误（Curl error 92），多个包（`git-core`、`gcc-c++`、`guile`）下载重试失败，最终 `guile` 包在所有镜像源中均无法下载，导致 `dnf` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → 克隆源码 → cmake 构建），`Dockerfile:6` 的 `dnf install -y git gcc gcc-c++ make cmake` 命令本身语法正确、包名有效。失败发生在网络传输层——`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在 HTTP/2 协议下对多个 RPM 包返回 `INTERNAL_ERROR`，属于 CI 基础设施/上游镜像站问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该失败是 `repo.openeuler.org` 镜像站 HTTP/2 传输层的间歇性问题，与代码无关。PR 的 Dockerfile 无需任何修改。等待镜像站恢复后重新触发 CI 构建即可，如果重试仍失败，可在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 或在 `/etc/dnf/dnf.conf` 中配置 `retries=5` 和 `timeout=30` 以提高容错能力。

### 方向 2（置信度: 低）
**降级为 HTTP/1.1。** 如果 `repo.openeuler.org` 的 HTTP/2 实现持续不稳定，可在 `dnf install` 前通过设置环境变量 `echo "http2=false" >> /etc/dnf/dnf.conf` 或在 curl 层面禁用 HTTP/2（`echo "http2=false" >> /etc/dnf/dnf.conf`）来绕过，但依赖底层 libcurl 对该配置的支持。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 架构上对 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务状态是否稳定
- 如果重试（rerun CI job）后仍然失败，需确认是否为仓库侧持续性问题而非间歇性故障
