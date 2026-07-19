# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在提供多个 RPM 包（cmake-data、git-core、gcc-c++）时反复出现 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），DNF 的重试机制在尝试所有镜像后仍然失败，导致 `gcc-c++` 包无法下载，整个 `dnf install` 命令退出。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 本身语法正确、依赖声明完整（与同类 GraDS 构建的 Dockerfile 结构一致）。失败完全由 openEuler 24.03-LTS-SP4 仓库镜像的网络层面 HTTP/2 协议问题引起（服务器端 HTTP/2 流异常关闭），属于 CI 基础设施问题，不是代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**直接重试 CI 构建**。本次失败是第三方仓库镜像 HTTP/2 协议层面的临时网络故障，不是代码问题。待仓库镜像恢复正常后重新触发 CI 构建即可通过。若多次重试仍失败，可检查仓库镜像站点的 HTTP/2 服务状态，或联系 openEuler 基础设施团队确认 `repo.****.org` 的可用性。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像）的 HTTP/2 服务是否已恢复正常。
- 若长期无法恢复，可考虑在 Dockerfile 的 `dnf install` 前配置备用镜像源或回退到 HTTP/1.1 协议。
