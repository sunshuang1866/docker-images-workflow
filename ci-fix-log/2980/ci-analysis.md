# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, dnf install, gcc-c++

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y …" did not complete successfully: exit code: 1
```

其他受影响的包（均自动恢复）：
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer … [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer … [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库镜像在本次构建期间存在间歇性 HTTP/2 流中断问题（Curl error 92），258 个待下载包中 3 个遭遇流错误，其中 2 个（cmake-data、git-core）重试后成功，`gcc-c++`（13 MB，较大包）两次重试均失败，耗尽所有镜像后 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增了一个面向 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套元数据，自身不包含任何可能导致网络/仓库错误的变更。`dnf install` 列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名（同一镜像在其他 PR 中曾正常安装），失败纯粹是镜像站 HTTP/2 服务端问题。

## 修复方向

### 方向 1（置信度: 高）
重试 CI 构建。该失败是仓库镜像的瞬态网络问题（HTTP/2 流错误），与代码无关。只需重新触发 CI job，在网络状况正常时构建即可通过。

## 需要进一步确认的点
- 如果多次重试均在同一包（`gcc-c++`）上失败，则可能是该 SPECIFIC 包在 openEuler 24.03-LTS-SP4 仓库镜像上的文件存在问题，需联系镜像站运维检查该文件完整性。
- 确认 CI 构建环境到 `repo.****.org` 的网络链路是否存在 HTTP/2 协议兼容性问题（代理/防火墙拦截 HTTP/2 流）。
