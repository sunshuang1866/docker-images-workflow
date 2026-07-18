# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像（`repo.****.org`）在下载 RPM 包时反复返回 HTTP/2 流错误（Curl error 92），多个包受影响（cmake-data、git-core、gcc-c++）。其中 cmake-data 和 git-core 重试后成功下载，但 `gcc-c++` 在两次重试均失败后耗尽所有镜像，最终 `dnf install` 报错退出。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，Dockerfile 中的 `dnf install` 命令语法正确、包名有效。失败完全是由于 openEuler 24.03-LTS-SP4 软件包仓库镜像的 HTTP/2 基础设施不稳定所致，属于 CI 运行时环境问题，重新触发构建有较大概率通过。

## 修复方向

### 方向 1（置信度: 高）
无需修改代码。该失败为 infra-error（软件包仓库镜像 HTTP/2 流不稳定），与 PR 变更无关。建议重新触发 CI 构建，网络状况改善后即可通过。

## 需要进一步确认的点
- 确认该仓库镜像（`repo.****.org`）的历史稳定性，如果频繁出现同类 HTTP/2 流错误，可能需要联系镜像运维团队排查或更换镜像源。
