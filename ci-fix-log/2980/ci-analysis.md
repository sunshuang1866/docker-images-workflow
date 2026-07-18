# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在 HTTP/2 传输层出现 `INTERNAL_ERROR (err 2)` 协议错误，导致 `gcc-c++` 等 RPM 包下载失败。`cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 经过多次重试仍未成功，最终耗尽所有镜像后构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2980 的改动仅为新增一个正确格式的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及配套的 README、image-info.yml、meta.yml 更新。Dockerfile 中的 `dnf install` 命令语法正确，所需软件包在仓库中确实存在（事务摘要列出了 258 个待安装包，下载总大小 914 MB）。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像网络的瞬时 HTTP/2 传输故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施的网络瞬时故障。触发重新构建（retry）即可解决。`gcc-c++` 包本身在仓库中是存在的（`gcc` 包在同一批次中下载成功），问题出在镜像站的 HTTP/2 连接稳定性上。

### 方向 2（置信度: 低）
如果重试多次仍然失败，可能需要在 Dockerfile 的 `dnf install` 前先更新 dnf 配置，禁用 HTTP/2 或增加重试次数/超时时间。但这是规避手段而非根治，仅供多次重试仍失败时参考。

## 需要进一步确认的点
- 如果重试（re-trigger CI）后问题解决，则确认为瞬时网络故障，无需任何代码变更。
- 如果重试后 x86_64 仍然失败，需检查 openEuler 24.03-LTS-SP4 仓库镜像站 `repo.****.org` 在 CI 构建时间段是否存在持续性的 HTTP/2 协议问题。
