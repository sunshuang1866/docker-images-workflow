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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多次遇到 HTTP/2 流层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`，`INTERNAL_ERROR (err 2)`）。其中 `cmake-data` 和 `git-core` 重试后恢复，但 `gcc-c++`（13 MB）在多次镜像重试后仍失败，最终 dnf 因"所有镜像均已尝试但未成功"而退出（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 内容在语法和依赖声明上均无问题——所列的 `gcc-c++` 等均为 openEuler 24.03-LTS-SP4 标准仓库中的合法包名。失败的直接原因是 CI 构建网络环境中镜像仓库服务器的 HTTP/2 连接不稳定，导致大文件（`gcc-c++` 13 MB）反复下载失败。同一批 `dnf install` 中也有其他包（cmake-data、git-core）出现相同的 `Curl error (92)`，表明这是仓库侧或网络中间件的系统性问题，与该 PR 的具体改动无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施/网络问题，应通过以下方式之一处理：
- **重试 CI 构建**：该错误为间歇性网络问题（日志中 cmake-data 和 git-core 重试后成功），重新触发 CI 构建大概率可成功。
- **检查仓库镜像状态**：联系 openEuler 24.03-LTS-SP4 仓库运维确认镜像服务器 HTTP/2 服务是否正常。若镜像端确实存在问题，需等待仓库侧修复。

### 方向 2（置信度: 低）
若重试仍持续失败且镜像仓库确认无问题，可考虑在 Dockerfile 的 `dnf install` 前增加 `dnf makecache` 或添加 `--setopt=retries=10` 等 dnf 重试参数。但这只是绕过网络问题的临时方案，不解决根因。

## 需要进一步确认的点
- 仓库 `repo.****.org`（日志中已脱敏）的 openEuler 24.03-LTS-SP4 OS 仓库 HTTP/2 服务当前是否正常运行。
- CI runner 所在网络到该仓库之间是否存在 HTTP/2 代理/CDN 拦截或篡改流量。
- 其他使用同一 openEuler 24.03-LTS-SP4 仓库的 PR 是否也出现了类似的 `Curl error (92)`（判断是否为仓库侧系统性问题）。
