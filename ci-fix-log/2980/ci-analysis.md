# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库镜像在 HTTP/2 传输过程中出现流帧错误（Curl error 92），导致 `cmake-data`、`git-core`、`gcc-c++` 三个包的下载被中断，其中 `gcc-c++` 重试所有镜像后仍失败，dnf 安装整体失败。属于 CI 构建环境的网络基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了一个标准格式的 Dockerfile（安装构建依赖 → 克隆源码 → 编译安装 GrADS），以及配套的 README、image-info.yml、meta.yml 更新。`dnf install` 命令中列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的合法软件包名，Dockerfile 语法和逻辑正确无误。本次失败与 PR 代码变更**完全无关**，是外部仓库镜像的网络临时故障。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该错误为 openEuler 24.03-LTS-SP4 软件仓库镜像 HTTP/2 传输层的瞬时故障，重新触发 CI 流水线即可。若短时间多次重试均失败，则需排查 CI Runner 到 `repo.****.org` 的网络连通性或该镜像服务的可用性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 OS 仓库镜像（`repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/`）在 CI 构建时段是否存在服务异常。
- 若持续出现同类错误，确认 CI Runner 的网络出口是否对 HTTP/2 协议有限制或存在中间代理设备干扰。
