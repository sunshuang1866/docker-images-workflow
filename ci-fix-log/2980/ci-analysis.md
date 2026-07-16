# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 流层错误（Curl error 92）。其中 cmake-data 和 git-core 在重试第三方仓库镜像后成功下载，但 gcc-c++（13MB）在所有重试机会耗尽后仍下载失败，导致整个 dnf 事务回滚。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 中 `dnf install` 命令列出的包名和语法均正确无误。失败的原因是 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 连接不稳定，属于 CI 基础设施/网络层面的瞬时故障。Dockerfile 本身的逻辑、包名、依赖关系均无问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为仓库镜像服务端 HTTP/2 协议层瞬时异常，`dnf install` 在下载大文件（如 gcc-c++ 13MB）时遭遇 HTTP/2 stream INTERNAL_ERROR，重试镜像后仍未成功。此类网络抖动导致的下载失败通常在重新运行 CI 后自动恢复，无需修改任何代码。

### 方向 2（置信度: 低）
若反复重试仍失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加重试机制（如 `dnf install -y --setopt=retries=10 ...`）或追加 `|| dnf install -y ...` 作为一次容错重试，增加对网络抖动的容忍度。但这仅作为防御性措施，当前阶段不建议添加。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像服务在 CI 构建时段的可用性是否正常（可通过手动 wget 测试 gcc-c++ 包 URL 验证）
- 确认是否仅本次构建遇到此问题，还是该仓库镜像近期持续不稳定
