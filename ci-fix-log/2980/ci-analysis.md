# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, stream was not closed cleanly

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
- 失败位置: Dockerfile:6（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件仓库镜像站（`repo.****.org`）的 HTTP/2 服务端存在流层错误（`INTERNAL_ERROR`），导致 `dnf install` 在下载 `gcc-c++` 等 RPM 包时 Curl 返回错误码 92（HTTP/2 流未正常关闭）。重试后所有镜像均尝试失败，`dnf` 终止安装。

### 与 PR 变更的关联
**与 PR 变更无关。** 这是 CI 基础设施问题——镜像仓库服务器端 HTTP/2 协议处理异常，属于网络/服务端瞬时故障。PR 新增的 Dockerfile 中 `dnf install` 的包列表均为 openEuler 24.03-LTS-SP4 标准仓库中的合法包名，语法正确。日志显示 `Dependencies resolved` 成功，258 个包的关系解析和 258 包均被 `dnf` 正确识别，问题纯属下载传输阶段的服务端错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 该失败属于 CI 基础设施的网络瞬时故障（镜像仓库 HTTP/2 服务端错误），与 PR 改动完全无关。Code Fixer 无需进行任何文件修改。建议直接重新触发 CI 构建（retry），待镜像站恢复后应能自动通过。

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像站当前 HTTP/2 服务是否已恢复正常（可联系运维确认或等待一段时间后重试）
- 如果多次重试均遇到同样的 HTTP/2 流错误，可能需要将 `dnf` 的下载协议降级为 HTTP/1.1（在 `dnf install` 前通过环境变量或 dnf 配置禁用 HTTP/2），但这属于 CI 基础设施层面的调整，不是 Dockerfile 的修改范围

## 修复验证要求
本失败为 infra-error，无需 code-fixer 提交代码修复。重新触发 CI 后可验证。
