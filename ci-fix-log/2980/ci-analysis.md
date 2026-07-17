# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 软件包镜像仓库（`repo.****.org`）在构建期间出现 HTTP/2 传输层协议错误（curl error 92: Stream error, INTERNAL_ERROR err 2），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载过程中 HTTP/2 stream 非正常关闭。`gcc-c++` 包在所有镜像均失败后被放弃，dnf 安装命令返回退出码 1。

### 与 PR 变更的关联

**与 PR 代码变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套的元数据文件（README.md、doc/image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确、包名合法。失败原因是 openEuler 24.03-LTS-SP4 的外部镜像仓库在构建时刻出现 HTTP/2 传输层抖动，属于 CI 基础设施问题。同样的 Dockerfile 在镜像仓库服务正常时应该能够成功构建。

## 修复方向

### 方向 1（置信度: 高）

**无需修改代码**。这是一个 CI 基础设施问题（infra-error），与 PR 的代码变更无关。建议直接触发 CI 重新运行（re-run/retry），在镜像仓库服务恢复正常后构建即可成功。

### 方向 2（置信度: 低）

如果镜像仓库持续不稳定，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 参数以增加重试次数，提高对临时网络波动的容忍度。但这属于锦上添花，不是本次失败的根本解决方案。

## 需要进一步确认的点

- 确认 openEuler 24.03-LTS-SP4 的 `repo.****.org` 镜像仓库当前状态是否正常（可能存在临时性服务降级）
- 如果是持续性故障，需要联系镜像仓库运维团队排查 HTTP/2 层的 INTERNAL_ERROR

## 修复验证要求

无需验证。本次失败为 infra-error，Code Fixer 无需处理。
