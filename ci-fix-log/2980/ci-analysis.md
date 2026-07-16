# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, dnf install, openEuler repo

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多次遭遇 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`）。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 包（~13MB）经历 2 次 HTTP/2 流错误后耗尽所有镜像重试次数，最终导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**此失败与 PR 变更无关。** PR 仅新增了一个 Dockerfile（含 `dnf install` 命令），Dockerfile 语法和包名均为正确。失败完全是由于 openEuler 24.03-LTS-SP4 仓库镜像服务器在构建时段的 HTTP/2 协议层不稳定，导致大文件下载在 HTTP/2 流层面被异常中断。这是一个纯 CI 基础设施/网络问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建。**

这是仓库镜像服务的临时性网络/协议问题。`gcc-c++` 包（约 13MB）的下载在 HTTP/2 流层面被中断，而其他包如 `cmake-data`（2.1MB）、`git-core`（11MB）虽也一度失败但在重试后成功。这说明镜像服务本身可用，只是在特定时段 HTTP/2 连接不稳定。等待镜像服务恢复后重新触发 CI 即可。

### 方向 2（置信度: 低）
如果同一 PR 多次重新触发后仍然失败，可能是 openEuler 24.03-LTS-SP4 仓库中 `gcc-c++-12.3.1-110.oe2403sp4` 包本身存在文件损坏或镜像同步不完整的问题，需联系 openEuler 基础设施团队检查该包在各镜像节点的一致性。

## 需要进一步确认的点
- 该 PR 是否在不同时间段多次触发后仍然失败？如果是，需排查仓库侧问题而非网络抖动。
- 其他同样使用 `openeuler:24.03-lts-sp4` 基础镜像的 Dockerfile（如同期其他 PR）是否也出现相同的 HTTP/2 流错误？如果是，则确认是仓库侧的系统性问题。
- openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在该时段是否有已知的服务中断或降级公告？
