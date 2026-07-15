# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf下载HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, MIRROR, guile, No more mirrors to try

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
- 失败位置: Dockerfile:6（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: aarch64 构建节点在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），其中 guile 包耗尽所有镜像重试后永久失败，导致整个 dnf 安装步骤退出码为 1。这是 CI 构建环境中 repo.openeuler.org 镜像站的网络/HTTP/2 协议层问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（以及配套的 README.md、image-info.yml、meta.yml 元数据更新），Dockerfile 中的 `dnf install` 命令格式与项目中其他 vvenc Dockerfile 一致，所列包名（git、gcc、gcc-c++、make、cmake）均为 openEuler 24.03-LTS-SP4 仓库中的有效包名。失败发生在 dnf 下载 RPM 包的网络传输阶段，PR 改动未引入任何导致此失败的因素。**本次失败与 PR 变更无关。**

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施/网络瞬时故障，Code Fixer 无需处理。建议重新触发 CI 构建。如果同一 runner（`ecs-build-docker-aarch64-04-sp`）持续出现同类 HTTP/2 错误，需排查该 runner 到 `repo.openeuler.org` 的网络连接或 HTTP/2 代理兼容性。

## 需要进一步确认的点
- 如果重试后仍然在 aarch64 runner 上失败，需确认 `repo.openeuler.org` 的 aarch64 包仓库是否有 HTTP/2 服务端问题
- 如果重试后通过，确认本次为瞬时网络故障
