# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 连接出现流错误（`Stream error in the HTTP/2 framing layer`，curl error 92），导致 RPM 包下载中断。多个包（cmake-data、git-core、gcc-c++）均遭遇此问题，其中 cmake-data 和 git-core 在重试后成功下载，但 gcc-c++（13 MB，较大）两次重试均失败，最终耗尽所有镜像重试次数，dnf 安装失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准格式的 Dockerfile（安装编译依赖 → 克隆源码 → 构建 GrADS），Dockerfile 本身语法正确、包名有效。失败完全由 CI 构建环境中 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 网络层问题导致，属于基础设施层面的瞬时故障。同一 PR 涉及的 README.md、image-info.yml、meta.yml 变更均为纯文档/元数据修改，不参与构建过程。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该类错误（Curl error 92，HTTP/2 stream INTERNAL_ERROR）为服务器端或中间网络设备的瞬时 HTTP/2 协议层问题，通常具有自愈性。在 CI 中重新触发构建（re-run），镜像仓库可能在本次重试时恢复正常，构建即可通过。

### 方向 2（置信度: 低）
**在 Dockerfile 中添加 dnf 重试参数**。若该镜像仓库的 HTTP/2 问题持续出现，可在 `dnf install` 命令中添加重试/超时参数（如 `--setopt=retries=10`），增加 dnf 对临时网络故障的容错能力。但这属于 workaround 而非根因修复，且对于 Curl error (92) 这类协议层错误，增加重试次数未必有效。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 流错误是否为持续性问题，还是仅该次构建的瞬时故障。建议在同一 x86_64 runner 上重新触发一次构建来确认。
- 如果多次重试均失败，需要排查仓库服务器的 HTTP/2 配置或中间代理/CDN 是否对 HTTP/2 连接有不当处理。
