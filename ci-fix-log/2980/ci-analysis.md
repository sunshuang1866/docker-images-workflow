# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, INTERNAL_ERROR

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方软件仓库镜像在本次构建期间存在 HTTP/2 传输层间歇性故障（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载遭遇 `Stream error in the HTTP/2 framing layer`。其中 cmake-data 和 git-core 经重试后成功，但 gcc-c++ 的两次重试均失败，最终 `No more mirrors to try`，dnf 安装步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增的 Dockerfile 内容完全正确——`dnf install` 命令语法无误、包名均有效、构建逻辑合理。失败纯粹是 openEuler 24.03-LTS-SP4 仓库镜像的网络基础设施问题：HTTP/2 连接流在传输大体积 RPM（gcc-c++ 13MB）时不稳定，导致 stream 异常关闭。日志中多个不同 RPM 包在不同 stream 上均出现同类错误，进一步排除包自身问题，确认根因在仓库服务端。

## 修复方向

### 方向 1（置信度: 高）
此失败为 **infra-error**，与 PR 代码无关。无需修改 Dockerfile 或任何代码文件。建议操作：
1. 等待 openEuler 仓库镜像恢复稳定后，在 CI 中重试（re-trigger）该 job。
2. 若该仓库镜像持续不稳定，可考虑在 Dockerfile 的 `dnf install` 命令中增加 `--retries 5` 或添加 `--setopt=retries=5` 参数，提高 dnf 对偶发网络错误的容忍度。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 的网络状态是否已恢复。可查看同一时间段内其他基于 24.03-lts-sp4 的 PR 构建是否也出现类似的 Curl error (92)。
- 若该仓库持续不稳定，确认 CI 环境是否可配置备用镜像站（如清华镜像站），通过 `dnf` 配置多镜像 fallback 提升下载可靠性。
