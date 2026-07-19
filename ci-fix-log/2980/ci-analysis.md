# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 官方仓库（`repo.*.org`）下载 RPM 包时，多次遭遇 HTTP/2 协议层面的流错误（Curl error 92: Stream error in the HTTP/2 framing layer, INTERNAL_ERROR）。其中 `cmake-data` 和 `git-core` 在重试后下载成功，但 `gcc-c++` 包在两次 HTTP/2 流错误后耗尽了所有镜像重试次数，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**无关。** 本次 PR 新增的 Dockerfile 语法正确，`dnf install` 中列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的有效包。日志中 258 个待安装包均已正确识别并开始下载，失败纯粹是由于下载过程中仓库镜像服务器的 HTTP/2 连接不稳定，属于 CI 基础设施问题，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败是 openEuler 24.03-LTS-SP4 仓库镜像的**临时性网络波动**导致的 HTTP/2 连接不稳定，属于 `infra-error`。Dockerfile 无需任何修改，等待仓库镜像恢复稳定后重试即可通过。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 官方仓库（`repo.*.org`）镜像服务在当前时间点的 HTTP/2 可用性是否已恢复。
- 如果多次重试后仍持续出现同类 HTTP/2 错误，需联系 openEuler 仓库运维团队排查 HTTP/2 层（如反向代理、负载均衡器）的配置问题。
