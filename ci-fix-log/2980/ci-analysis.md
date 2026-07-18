# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo mirror

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
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像服务器在处理 HTTP/2 请求时发生内部错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等 3 个 RPM 包下载失败，`dnf` 在重试所有镜像后仍无法下载而报错退出。**该错误发生在 3 个不同包上（cmake-data、git-core、gcc-c++）且均为同源 `repo.****.org`，确认为仓库镜像服务端问题，非 PR 代码或包本身的问题。**

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 中 `dnf install` 的包列表和语法均正确，失败完全由外部 RPM 仓库镜像的 HTTP/2 协议栈故障导致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是典型的 CI 基础设施问题（infra-error）。openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在构建时出现 HTTP/2 流错误，属于仓库服务端间歇性故障。建议：
- 等待仓库镜像恢复后重新触发 CI 构建
- 如问题持续出现，联系 openEuler 镜像站运维排查 HTTP/2 协议栈配置

## 需要进一步确认的点
- 仓库镜像 `repo.****.org` 的 HTTP/2 错误是否为持续性问题或已恢复（可重新触发 CI 验证）
- 是否只有 x86_64 架构的特定包（gcc-c++、cmake-data、git-core）受影响，还是整个仓库镜像存在普遍问题

## 修复验证要求
无。本失败为 infra-error，`code-fixer` 无需处理。
