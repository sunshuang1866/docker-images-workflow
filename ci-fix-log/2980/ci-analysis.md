# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, INTERNAL_ERROR (err 2), Cannot download, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像站存在 HTTP/2 传输层问题，多个 RPM 包（cmake-data、git-core、gcc-c++）下载时遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，其中 gcc-c++ 在所有镜像源均重试失败，导致 dnf 安装步骤整体失败。该问题属于 CI 基础设施/上游仓库的网络瞬态故障，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 变更仅新增了 grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（以及 README.md、image-info.yml、meta.yml 文档更新）。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 仓库中存在的合法包名。失败原因是上游软件仓库镜像站 HTTP/2 传输异常，属于 CI 基础设施问题，不是 PR 代码逻辑错误。

## 修复方向

### 方向 1（置信度: 中）
**重试触发 CI 构建**。由于该错误是上游仓库镜像站的网络瞬态故障（HTTP/2 stream 未正常关闭），dnf 自身已尝试了所有可用镜像源均失败。重新触发 CI 构建流水线，在新的一次尝试中网络状态可能恢复正常，构建即可通过。无需修改任何代码或 Dockerfile。

### 方向 2（置信度: 低）
**配置 dnf 使用 HTTP/1.1 替代 HTTP/2**。如果该仓库镜像站持续出现 HTTP/2 相关问题，可在 Dockerfile 的 dnf install 之前添加 dnf 配置，将 `max_parallel_downloads` 降低或将传输协议降级为 HTTP/1.1。但此方向不推荐——它无法从根本上解决镜像站的问题，且属于为基础设施问题添加不必要的构建配置。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站在 CI 构建时段的网络状态是否正常（是否为临时性波动）
- 重新触发 CI 构建后是否仍然失败——若连续多次失败，需排查是否仓库镜像站对特定 IP 段有访问限制或 HTTP/2 配置存在问题

## 修复验证要求
无需验证——本失败为 infra-error，Code Fixer 无需处理任何代码修改。建议由 CI 管理员检查仓库镜像站网络状态后重新触发构建。
