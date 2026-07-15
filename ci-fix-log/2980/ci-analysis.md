# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, No more mirrors to try

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
- 失败位置: Dockerfile:6（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境访问 openEuler 24.03-LTS-SP4 仓库镜像时，HTTP/2 连接层出现协议帧错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 包下载失败。该包经过两次镜像重试均以相同错误失败，dnf 耗尽所有可用镜像后终止构建。其他包（cmake-data、git-core）也遇到同类 HTTP/2 错误，但在后续重试中成功下载。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个符合项目规范的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`），`dnf install` 命令语法和包列表均正确，遵循了仓库中同类镜像的一致模式。失败原因为 CI 基础设施与 openEuler 24.03-LTS-SP4 仓库镜像之间的 HTTP/2 协议层网络故障，属于 transient infra 问题，Code Fixer 无需处理 Dockerfile 代码。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 CI 基础设施的网络问题——构建节点与 openEuler 24.03-LTS-SP4 仓库镜像之间的 HTTP/2 连接出现了协议帧错误。建议：
1. 重新触发 CI 构建（retry），如果镜像仓库端网络恢复，构建应能成功
2. 如果反复出现，联系 CI 运维排查仓库镜像代理/缓存的 HTTP/2 配置，或者将 dnf 配置为使用其他远端仓库源进行构建

## 需要进一步确认的点
- 确认 CI 构建环境配置的 openEuler 24.03-LTS-SP4 仓库镜像地址（日志中为 `repo.****.org`）在当前时间段是否存在可复现的 HTTP/2 协议异常
- 确认该仓库镜像是否支持回退到 HTTP/1.1 作为备选协议
