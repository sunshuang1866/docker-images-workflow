# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, INTERNAL_ERROR (err 2)

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在处理 HTTP/2 请求时频繁出现 Stream error（`Curl error (92): INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等关键包下载失败。`cmake-data` 和 `git-core` 经过重试后恢复下载，但 `gcc-c++` 的两个镜像均返回相同 HTTP/2 流错误，最终所有镜像尝试完毕仍无法下载，`dnf install` 失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 命令中列出的包在仓库元数据中均已存在（从日志可见 Dependencies resolved 阶段列出了所有 258 个待安装包，包括 `gcc-c++`）。失败原因是 CI 构建环境访问 openEuler 24.03-LTS-SP4 仓库镜像时遇到 HTTP/2 协议层传输错误，属于临时的基础设施/网络问题，重试构建可大概率通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 CI 基础设施的临时网络问题（openEuler 仓库镜像 HTTP/2 流不稳定），Code Fixer 无需处理。建议触发 re-run 重试构建，等待仓库镜像恢复稳定。

### 方向 2（仅当重试持续失败，置信度: 低）
如果多次重试后 `gcc-c++` 下载仍然失败，可考虑在 `dnf install` 前添加重试机制，或设置 `dnf` 的 `max_retries` 和 `timeout` 参数以提高容错能力。但这是绕行方案，不应作为首选。

## 需要进一步确认的点
- 检查 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在失败时段的可用性状态
- 确认同时间段其他依赖 openEuler 24.03-LTS-SP4 仓库的 CI 构建是否也遭遇了同样的 HTTP/2 流错误（以确认是否为仓库端问题而非单点网络抖动）
