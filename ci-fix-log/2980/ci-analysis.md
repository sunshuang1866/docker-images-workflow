# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler SP4 仓库下载失败
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

#7 ERROR: process "/bin/sh -c dnf install -y ... gcc-c++ ... git && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（第 6 行的 `RUN dnf install` 指令）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库在 CI 构建时出现 HTTP/2 流传输错误（Curl error 92），多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）在下载过程中因 HTTP/2 stream INTERNAL_ERROR 而中断。前两个包在重试后成功下载，但 `gcc-c++` 在两次失败后耗尽了所有备用镜像，最终导致整个 `dnf install` 事务失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 这是一个纯基础设施/网络层故障：
- PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，依赖包列表完整。
- `cmake-data`（成功重试）和 `git-core`（成功重试）的同类错误证明问题出在仓库端 HTTP/2 协议处理，而非特定包缺失或包名错误。
- `gcc-c++` 包在 SP4 仓库中确实存在（`12.3.1-110.oe2403sp4` 出现在依赖解析清单中），仅是网络传输失败。
- 本次 PR 变更范围仅限于新增 `Others/grads/` 目录下的 Dockerfile 和 README/meta 等文档文件，不涉及任何基础设施配置修改。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为 openEuler SP4 仓库镜像瞬态网络故障，重试后大概率自动恢复。从日志中可以看到 `cmake-data` 和 `git-core` 的同类 `Curl error (92)` 均在重试后成功下载，`gcc-c++` 只是不幸在两次重试后仍未成功。

## 需要进一步确认的点
- 无。日志证据充分，根因明确：openEuler 24.03-LTS-SP4 仓库在构建时刻的 HTTP/2 传输层不稳定，非 PR 代码问题。
