# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输中断
- 新模式症状关键词: Curl error (92), HTTP/2, Stream error, INTERNAL_ERROR, No more mirrors to try, dnf install

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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库镜像下载 `gcc-c++` RPM 包时，HTTP/2 传输层多次出现流错误（`Curl error 92: HTTP/2 stream not closed cleanly: INTERNAL_ERROR`），重试耗尽所有镜像后下载失败，导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 改动无关。** 本次 PR 仅新增一个格式正确的 Dockerfile、README.md 表项、`image-info.yml` 表项和 `meta.yml` 条目，无代码逻辑错误。失败完全由 CI 构建环境与 openEuler 仓库镜像之间的 HTTP/2 网络传输问题引起。同类 HTTP/2 流错误同时影响 `cmake-data` 和 `git-core` 包（后者成功在重试后下载完成），表明该仓库镜像在构建时段存在网络不稳定。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 构建即可。** 这是 CI 仓库镜像的临时性网络问题，PR 新增的 Dockerfile 本身没有错误。建议在非高峰时段重新触发 CI 构建（rerun），若仓库镜像恢复稳定，构建应当成功。

### 方向 2（置信度: 低）
若反复重试仍失败，考虑在 Dockerfile 的 `dnf install` 前配置备用镜像源或添加重试参数（如 `dnf install --setopt=retries=10`），但鉴于这是基础设施层的问题，代码层面缓解手段有限。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 官方仓库镜像（`repo.****.org`）在构建时段（2026-07-13 07:04 UTC）是否存在已知的网络故障或 HTTP/2 代理兼容性问题。
- 若重试后仍然失败，需确认是否所有 x86_64 runner 节点对该仓库的 HTTP/2 连接均有问题，或仅限于 `ecs-build-docker-x86-03-sp` 节点。
