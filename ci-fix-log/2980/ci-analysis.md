# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, openEuler

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在 Docker 构建期间出现 HTTP/2 协议层内部错误（`INTERNAL_ERROR`），导致 `gcc-c++` RPM 包下载失败。虽然 `cmake-data` 和 `git-core` 在镜像重试后成功下载，但 `gcc-c++` 两次尝试（HTTP/2 stream 65 和 83）均被服务端异常关闭，最终 dnf 耗尽所有可用镜像后报错退出。

### 与 PR 变更的关联
此次失败与 PR 的代码变更 **无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名（日志中依赖解析阶段全部识别成功）。失败是仓库镜像服务器的临时性网络/协议故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。该失败为基础设施层面的短暂故障。直接重新触发 CI 构建（retry）即可，新构建大概率会因为仓库镜像恢复而成功。若高频重试仍失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache --refresh` 或增加 `--retries N` 等重试参数来增强网络波动下的鲁棒性。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库在构建时段是否有服务降级或维护公告。
- 如果 retry 后仍然失败，需要确认 `gcc-c++-12.3.1-110.oe2403sp4.x86_64` 这个特定 RPM 包在仓库中是否被移除或替换为更新版本。

## 修复验证要求
不涉及正则 patch 外部源文件，无需验证。
