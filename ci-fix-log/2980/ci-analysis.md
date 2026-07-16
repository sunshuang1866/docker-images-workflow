# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, stream was not closed cleanly, No more mirrors to try, repo.***.org

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建节点从 openEuler 24.03-LTS-SP4 官方仓库（`repo.****.org`）下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 流层协议错误（Curl error 92: `INTERNAL_ERROR`）。`gcc-c++` 在重试两次后耗尽所有镜像，`dnf` 因无法下载该包而终止构建。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（以及 README、image-info.yml、meta.yml 的描述更新）。Dockerfile 中的 `dnf install` 命令及其包列表语法和内容完全正确。失败是由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端协议错误引起的，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该失败是 openEuler 24.03-LTS-SP4 仓库镜像的瞬时网络/服务端 HTTP/2 协议问题（Curl error 92: INTERNAL_ERROR），多个不同 RPM 包的下载均被同一类型的流层错误中断。此类问题通常由镜像站暂时不稳定导致，具有自愈性。Code Fixer 无需处理，在 CI 中重新触发构建即可。

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像站的 HTTP/2 服务是否已恢复正常（可尝试手动 `curl` 下载失败的 `gcc-c++` 包验证）
- 如果多次重试仍失败，考虑在 Dockerfile 中为 `dnf` 添加重试参数（如 `--setopt=retries=10`），或临时切换到其他镜像源
