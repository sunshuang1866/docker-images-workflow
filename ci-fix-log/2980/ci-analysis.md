# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, gcc-c++

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 HTTPS/HTTP2 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，多次遭遇 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），涉及 `cmake-data`、`git-core`、`gcc-c++` 三个软件包。其中 `gcc-c++` 在所有镜像源均重试失败，最终导致 dnf 安装阶段不可恢复地失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 中列出的软件包名称均存在于 openEuler 24.03-LTS-SP4 仓库中（从日志中 `Dependencies resolved` 部分可确认 `gcc-c++` 包被正确识别为 `gcc-c++-12.3.1-110.oe2403sp4`，架构为 `x86_64`）。失败纯粹是 CI 构建时 openEuler 软件仓镜像站的 HTTP/2 连接不稳定导致的网络问题，属于基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 这是 CI 基础设施侧的临时网络故障（HTTP/2 stream 异常中断），与 PR 代码无关。等待 openEuler 仓库镜像站恢复稳定后，重新触发 CI 构建大概率会通过。Code Fixer 无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 低）
如果反复重试仍然在同一批 RPM 包上失败，可在 `dnf install` 命令前增加重试/回退逻辑（如设置 `--retries` 或切换至备用镜像源），但这属于治标方案，性价比低，通常不需要。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）在构建时的可用性状态，以及其 HTTP/2 层是否存在已知问题。
- 确认 CI 构建节点的网络出口是否存在中间代理或防火墙干扰 HTTP/2 连接。
- 由于 `Finished: FAILURE` 明确出现在日志末尾，且错误信息直接来自构建步骤，日志不属于 trigger/编排层，本次分析证据充分，无需获取其他下游 job 日志。
