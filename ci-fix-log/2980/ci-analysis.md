# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, gcc-c++

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 行）
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 仓库镜像在通过 HTTP/2 下载 RPM 包时出现流层协议错误（`Curl error 92`），导致 `gcc-c++` 包的两次镜像重试均失败，`dnf install` 最终因"No more mirrors to try"而退出。三个包（`cmake-data`、`git-core`、`gcc-c++`）均短暂遭遇此问题，前两者在重试后成功，仅 `gcc-c++` 在两次重试后仍未成功。这是 CI 基础设施与上游仓库之间的网络/协议层瞬时故障，与 Dockerfile 中的包名或版本无关。

### 与 PR 变更的关联
PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及其元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 仓库中的有效包名（dnf 已成功解析全部 258 个包的依赖关系并开始下载，38 个包成功下载后才在 `gcc-c++` 上失败）。此失败与 PR 代码变更**无关**，是 CI 基础设施层面的瞬时网络故障。

## 修复方向

### 方向 1（置信度: 高）
无需修改 Dockerfile 或任何代码。这是 CI 基础设施（仓库镜像 HTTP/2 连接）的瞬时故障，重新触发 CI 构建即可。如果该问题反复出现，可能需要从 CI 侧排查：
- openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务稳定性
- CI runner 到仓库的网络链路质量
- 是否需要在 dnf 配置中限制使用 HTTP/1.1 作为临时规避手段

## 需要进一步确认的点
- 该仓库镜像的 HTTP/2 流错误是偶发还是持续性问题：可通过重新触发 CI 构建（Rerun）来验证。如果重试后通过，则为瞬时故障；如果持续相同错误，需排查仓库侧或网络侧问题。
- 如果重试后仍失败，需检查 `dnf` 是否可通过配置降级为 HTTP/1.1 以规避 HTTP/2 协议层的不兼容。
