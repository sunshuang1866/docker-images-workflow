# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 传输错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在通过 DNF 从 openEuler 24.03-LTS-SP4 仓库镜像站下载 RPM 包时，遭遇持续性的 HTTP/2 传输层 `INTERNAL_ERROR` (`Curl error 92`)。该错误影响了多个包（`cmake-data`、`git-core`、`gcc-c++`），其中 `cmake-data` 和 `git-core` 在 DNF 自动重试后成功下载，但 `gcc-c++` 两次重试均失败，最终所有镜像尝试耗尽，`dnf install` 退出码为 1，导致 Docker 构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 本身语法正确、包名有效、`dnf install` 命令格式规范。失败原因是 openEuler 24.03-LTS-SP4 官方仓库镜像在 CI 构建时段的 HTTP/2 服务不稳定，属于 CI 基础设施/上游服务问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**直接重试 CI 构建。** 该错误为 openEuler 仓库镜像 HTTP/2 服务的暂时性故障，属于外部基础设施问题。DNF 在日志中已对 `cmake-data` 和 `git-core` 完成了自动重试和恢复，仅 `gcc-c++` 的两次重试均落在故障窗口内。等待仓库镜像恢复后重新触发 CI 构建即可通过，无需修改任何代码。

### 方向 2（置信度: 中）
**调整 DNF 配置降低 HTTP/2 依赖。** 如果该仓库镜像的 HTTP/2 问题频繁复现（非单次偶发），可考虑在 Dockerfile 的 `dnf install` 前添加 DNF 配置步骤（如设置 `http2=false` 强制使用 HTTP/1.1，或增加 `max_retries` 重试次数），以规避 HTTP/2 传输层的不稳定性。但鉴于当前仅为单次构建失败，暂不建议为此引入非必要的配置变更。

## 需要进一步确认的点
- 该仓库镜像（`repo.****.org`）的 HTTP/2 服务是否在 CI 构建时段存在已知故障或维护窗口。
- 同一时间段内其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现类似 HTTP/2 stream error——可据此判断是全局性镜像站故障还是单次波动。
- 若重试后依旧失败，需排查是否有防火墙/代理层干扰 HTTP/2 长连接（如连接被中间设备 RST）。
