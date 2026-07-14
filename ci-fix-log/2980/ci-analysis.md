# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, gcc-c++, repo.****.org

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在下载 RPM 包时出现间歇性 HTTP/2 协议层错误（Curl error 92: Stream error in the HTTP/2 framing layer）。多个包（`cmake-data`、`git-core`、`gcc-c++`）均触发了此错误。其中 `cmake-data` 和 `git-core` 重试后下载成功，但 `gcc-c++` 经过 2 次尝试均失败，导致 dnf 安装整体失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是一个 CI 基础设施/网络问题。PR 新增的 Dockerfile 内容本身正确——使用的包名（`gcc-c++`、`cmake`、`readline-devel` 等）均为 openEuler 标准包名，`dnf install` 命令语法也与其他同类 Dockerfile 一致。失败原因是对应 openEuler 24.03-LTS-SP4 版本的软件包仓库 CDN/镜像节点在构建时出现 HTTP/2 流异常，属临时性网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此失败为临时性仓库镜像网络故障，PR 代码本身无误。等待 openEuler 24.03-LTS-SP4 仓库镜像恢复后，重新触发 CI 流水线大概率可通过。无需修改任何代码。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）当前网络健康状况，是否存在持续的 HTTP/2 协议问题。
- 若多次重试均失败，需排查 CI 构建节点到该仓库镜像的网络链路（是否需切换镜像源或调整网络配置）。
