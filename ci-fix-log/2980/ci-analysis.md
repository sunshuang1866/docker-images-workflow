# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-c++, openEuler-24.03-LTS-SP4

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

#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在通过 HTTP/2 协议下载 RPM 包时返回流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），导致 `gcc-c++` 包在多次重试后仍下载失败。`cmake-data` 和 `git-core` 也出现过同类错误但重试成功，仅 `gcc-c++`（13MB）因文件较大且多次 HTTP/2 流中断而彻底失败。

### 与 PR 变更的关联
PR 变更为新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，Dockerfile 内容本身（`dnf install` 包列表、configure 参数等）与同软件的 sp3 版本一致，写法正确。失败与代码变更**无直接关系**——这是 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 协议层面问题，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 中）
在 `dnf install` 命令前禁用 HTTP/2，强制使用 HTTP/1.1 下载以规避仓库镜像的 HTTP/2 流错误：
- 方式 A：设置 `echo "http2=false" >> /etc/dnf/dnf.conf` 将 dnf/curl 全局回退到 HTTP/1.1
- 方式 B：通过环境变量 `RUST_LOG=curl=off` 或在 curl 层面禁用 HTTP/2

### 方向 2（置信度: 低）
直接重试 CI job——HTTP/2 流错误可能是仓库镜像临时的协议层故障，下一次构建可能不再复现。若重试后仍失败，则说明 SP4 仓库镜像的 HTTP/2 实现有持续性问题，需按方向 1 处理。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库镜像是否长期存在 HTTP/2 协议兼容性问题，还是当次构建时的偶发故障
2. 该 PR 的其他架构 job（如 aarch64）是否也遇到同类错误
3. 同一天其他 PR 中对 SP4 仓库的 dnf 操作是否同样失败（可判断是否为仓库侧问题）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（无需填写，本失败不涉及正则 patch 外部源文件）
