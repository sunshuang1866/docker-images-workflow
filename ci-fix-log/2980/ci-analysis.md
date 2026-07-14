# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在 HTTP/2 传输层出现多次流中断错误（Curl error 92），导致 `gcc-c++`（13 MB）等 RPM 包下载失败并耗尽所有镜像重试。`cmake-data` 和 `git-core` 虽也遇到同类错误但重试后成功，`gcc-c++` 因文件较大重试两次后所有镜像均不可用。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 grads 的 Dockerfile 及配套元数据文件（Dockerfile、README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法和包名均正确。失败原因为 CI 构建时 openEuler 24.03-LTS-SP4 软件源镜像出现临时的 HTTP/2 传输层故障，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 软件源镜像的临时网络故障（HTTP/2 stream INTERNAL_ERROR），建议触发 CI 重试（retrigger）即可。`gcc-c++` 包在两次重试后镜像耗尽，但该类 HTTP/2 流错误通常为瞬态问题，下一次构建时大概率恢复正常。

## 需要进一步确认的点
无。日志证据充分，根因明确为软件源 HTTP/2 传输层错误，与 PR 代码无关。
