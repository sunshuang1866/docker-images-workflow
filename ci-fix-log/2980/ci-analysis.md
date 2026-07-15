# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: DNF 镜像源 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-c++

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境通过 `dnf` 从 openEuler 24.03-LTS-SP4 仓库源下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时，多次遭遇 HTTP/2 协议层 `INTERNAL_ERROR`（Curl error 92），dns 的重试机制耗尽所有镜像后仍失败。同时，`cmake-data` 和 `git-core` 也遭遇过同类 HTTP/2 流错误，但通过重试成功恢复。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（含 `dnf install` 构建依赖步骤）和配套的 README、image-info.yml、meta.yml 元数据文件。Dockerfile 中的 `dnf install` 命令语法正确，包名与 openEuler 24.03-LTS-SP4 仓库匹配（日志中 DNF 已成功解析 258 个软件包依赖关系）。失败源于构建环境与 openEuler 仓库镜像站之间的 HTTP/2 协议通信不稳定，属于 CI 基础设施/网络层面的问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）通常是临时的网络或服务端问题。如果是间歇性的，重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
**配置 DNF 使用 HTTP/1.1 协议**。在 `dnf install` 前添加 DNF/Curl 配置，强制使用 HTTP/1.1 而非 HTTP/2，以规避 H2 协议层的 INTERNAL_ERROR。这需要在 Dockerfile 的 RUN 中增加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或类似配置。

### 方向 3（置信度: 低）
**配置 DNF retries 参数**。在 `dnf install` 前通过 `echo "retries=10" >> /etc/dnf/dnf.conf` 增加 DNF 重试次数，提高对网络波动的容忍度。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库源（`repo.****.org`）在 CI 构建环境中是否持续存在 HTTP/2 稳定性问题，还是本次为偶发故障。
2. 同一 PR 中其他架构（aarch64）的构建 job 是否也遇到相同问题——如果仅 x86_64 失败，可能是该镜像源特定节点的 H2 配置问题。
3. 该仓库其他使用 openEuler 24.03-LTS-SP4 基础镜像的 Dockerfile 近期是否也出现同类 dnf 下载失败——如果是，说明需要仓库层面统一调整 dnf 配置。
