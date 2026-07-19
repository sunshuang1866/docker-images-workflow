# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流中断
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库镜像服务器的 HTTP/2 流多次异常中断（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等包重试耗尽所有镜像后下载失败，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（含 `dnf install` 安装编译依赖的标准步骤）和相关的元数据文件（`README.md`、`image-info.yml`、`meta.yml`）。`dnf install` 命令中列出的所有包名均为 openEuler 24.03-LTS-SP4 官方仓库中的有效包——日志中的 "Dependencies resolved" 部分已确认 RPM 依赖解析成功，包列表正常。失败完全由 CI 构建环境的 openEuler 仓库镜像服务器在传输大文件（如 34 MB 的 `gcc`、13 MB 的 `gcc-c++`）时 HTTP/2 连接不稳定所致，属于 CI 基础设施（infra/proxy）的瞬时网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 该失败为 CI 基础设施的网络瞬时故障，PR 代码无任何问题。建议直接重新触发 CI 构建流水线。大多数情况下，仓库镜像服务器的 HTTP/2 连接问题不会在重试中复现。

### 方向 2（置信度: 低）
若多次重试均因相同原因失败，说明 openEuler 24.03-LTS-SP4 仓库镜像持续不稳定。可在 Dockerfile 中为 `dnf` 添加重试参数（如 `dnf install -y --setopt=retries=10`）提高网络容错能力。但不建议针对一次性的 infra 问题修改代码。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的仓库镜像（`repo.****.org`）在该 CI 构建时段是否存在已知的 HTTP/2 服务异常。
- 若同一时段其他 PR 的 x86_64 构建也失败，则可进一步确认为镜像服务临时故障。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（无——本次失败为 infra-error，无需代码修复。）
