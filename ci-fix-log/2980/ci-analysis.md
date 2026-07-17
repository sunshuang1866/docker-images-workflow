# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 仓库镜像流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6（`dnf install` 步骤）
- 失败原因: CI 构建环境的 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 HTTP/2 传输层出现服务端流错误（`INTERNAL_ERROR`），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。dnf 重试所有可用镜像后均告失败，最终 `gcc-c++` 包无法下载，整个 `dnf install` 命令返回错误码 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅为新增一个 GraDS 2.2.3 在 openEuler 24.03-LTS-SP4 上的标准 Dockerfile，其 `dnf install` 命令中列出的全部是 openEuler 官方仓库的标准系统包（gcc、cmake、各种 -devel 包等），语法正确无误。失败的直接原因是 CI 构建过程中 `repo.****.org` 的 HTTP/2 连接不稳定，服务端返回 `INTERNAL_ERROR`（属于服务端/网络层面的瞬时故障），并非 Dockerfile 内容或 PR 变更所导致。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是典型的 CI 基础设施瞬时故障（HTTP/2 流层面的服务端内部错误），与代码无关。等待仓库镜像恢复后重新触发 CI 构建即可。如果同类问题频繁出现，可联系 CI 运维团队排查 `repo.****.org` 镜像站的 HTTP/2 服务稳定性，或考虑在 Dockerfile 中为 dnf 添加 `--retries` / `--setopt=retries=10` 参数提高容错能力。

## 需要进一步确认的点
- 确认 `repo.****.org` 镜像站在构建时刻是否存在已知的服务降级或网络抖动。
- 如果重试后仍持续失败，需要检查仓库镜像站是否对特定 RPM 包（如 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`）存在损坏或发行异常。
