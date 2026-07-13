# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, No more mirrors to try, gcc-c++

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 软件仓库多个镜像站在 HTTP/2 传输层出现流中断错误（Curl error 92: INTERNAL_ERROR），其中 `cmake-data` 和 `git-core` 重试后下载成功，但 `gcc-c++` 在耗尽全部镜像站后仍然失败，导致 `dnf install` 退出码为 1。

### 与 PR 变更的关联
与 PR 改动无关。PR 新增的 Dockerfile 中 `dnf install` 的包名和语法均正确，与已有的 `24.03-lts-sp3` 版本 Dockerfile 使用相同模式。失败原因是 openEuler SP4 仓库镜像站在构建时段的 HTTP/2 传输层出现了临时性网络错误，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是一个临时性基础设施问题，无需修改代码。建议直接触发 CI 重试（re-run），等待仓库镜像站 HTTP/2 连接恢复正常即可。从日志看 `cmake-data` 和 `git-core` 在重试后成功下载，说明问题本质是可自愈的网络波动。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站在当前时段是否稳定（可检查仓库健康状态页面）
- 如果重试多次后仍然失败，需要确认是否是特定镜像站永久性故障，此时可能需要更换基础镜像中的 repo 源配置

## 修复验证要求
无需修改代码，无验证要求。
