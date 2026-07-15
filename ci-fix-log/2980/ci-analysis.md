# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在下载多个 RPM 包时出现 HTTP/2 流层错误（curl error 92: `Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` 等多个包下载失败，`dnf` 在重试所有可用镜像后宣告失败

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、包名有效（共 258 个包已在依赖解析阶段通过），失败完全由 openEuler 仓库镜像的网络/HTTP/2 协议层问题引起。日志显示多个 RPM 包（cmake-data、git-core、gcc-c++）在不同 HTTP/2 stream 上均遭受相同的 stream 中断错误，说明这是仓库服务器端的 transient 问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。此失败是 CI 基础设施的暂态网络问题（openEuler 仓库镜像服务器 HTTP/2 流异常中断），Dockerfile 本身无问题。等待仓库镜像恢复后重新触发 CI 构建即可通过。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像当前是否恢复正常（可直接在 CI runner 环境中运行 `curl -I https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/` 测试连接性）
- 如果该问题频繁复现，可能需要考虑为 `dnf install` 添加 `--retries` 参数或切换到其他可用镜像源
