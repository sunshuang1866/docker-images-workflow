# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库服务器多次出现 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），其中 `gcc-c++` 包在所有镜像重试后仍然失败，导致整个 `dnf install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 命令中列出的所有依赖包名称（`gcc gcc-c++ make cmake ...`）均为 openEuler 仓库中实际存在的合法包名（日志中 Dependencies resolved 和 Transaction Summary 阶段正确解析了所有 258 个包的依赖关系）。失败纯粹是因为 openEuler 24.03-LTS-SP4 仓库服务器在下载阶段发生了间歇性 HTTP/2 传输层错误，属于 CI 基础设施网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 此失败是仓库服务器侧临时的 HTTP/2 传输层故障，与代码无关。重新触发 CI 构建即可（可能需要等待仓库侧问题恢复后重试）。如果反复重试仍然失败，可考虑在 Dockerfile 的 `dnf install` 前增加重试逻辑或切换到备选镜像源。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库服务器（`repo.****.org`）当前是否存在稳定性问题，可通过 `curl -I` 直接访问相关 RPM 包的 URL 验证。
- 该仓库的 HTTP/2 配置是否存在已知的互操作性问题（某些 dnf/libcurl 版本与特定 HTTP/2 服务器实现不兼容）。
