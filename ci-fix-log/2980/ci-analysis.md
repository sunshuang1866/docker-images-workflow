# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-c++, dnf install

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
- 失败原因: Docker 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13 MB）时，上游镜像服务器反复返回 HTTP/2 帧层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），重试耗尽所有镜像后下载失败。同时，`cmake-data` 和 `git-core` 两个包也遭遇了同类 HTTP/2 流错误，但重试后成功下载；仅 `gcc-c++` 包因连续两次 HTTP/2 错误最终完全失败。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增了一个 `Dockerfile`（GrADS 2.2.3 + openEuler 24.03-LTS-SP4）、更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 中的 `dnf install` 命令格式正确、依赖包列表完整，失败原因是 CI 构建环境与 openEuler 24.03-LTS-SP4 仓库镜像之间的网络/HTTP 协议层问题，属于基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 这是 openEuler 24.03-LTS-SP4 仓库镜像服务器的临时性 HTTP/2 流错误（`INTERNAL_ERROR`），非 PR 代码引起。多个包（cmake-data、git-core、gcc-c++）均出现同类错误，且 cmake-data 和 git-core 在重试后成功，说明问题为间歇性网络故障。建议等待镜像服务器恢复后重新触发 CI 构建。

## 需要进一步确认的点
- 如果多次重试 CI 仍然失败，需排查 CI 构建节点（`ecs-build-docker-x86-03-sp`）到 `repo.****.org` 之间的网络链路是否存在持续性问题。
- 确认 openEuler 24.03-LTS-SP4 仓库镜像服务端是否有 HTTP/2 协议相关的已知缺陷或配置变更。
