# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 RPM 仓库下载软件包时，多个包遭遇 HTTP/2 流层错误（Curl error 92）。其中 `cmake-data` 和 `git-core` 在重试后恢复，但 `gcc-c++`（13 MB）经过两次重试后耗尽所有镜像源，最终下载失败，导致整个 `dnf install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅为新增 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）和配套元数据文件（`meta.yml`、`README.md`、`image-info.yml`），未修改仓库源配置。失败是 CI 构建时 openEuler RPM 仓库的 HTTP/2 服务端临时性故障所致，属于基础设施层面的瞬时网络问题。任何在此时段尝试安装相同 RPM 包的构建任务都会遇到相同错误。

## 修复方向

### 方向 1（置信度: 高）
无需修改任何代码。这是 RPM 仓库服务器的瞬时网络故障，`dnf install` 中 `cmake-data` 和 `git-core` 在重试后已成功下载，说明问题仅影响特定时段的特定连接。**重新触发 CI 构建**大概率会通过。如果在 CI 流程中允许，可以在 `dnf install` 前添加 `dnf makecache` 或设置 `--retries` 选项以增强重试容忍度，但非必须。

## 需要进一步确认的点
无。日志证据充分，根因明确为 RPM 仓库 HTTP/2 连接层故障，与 PR 代码变更无关。
