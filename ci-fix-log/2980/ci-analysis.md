# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建环境在通过 `dnf install` 从 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像下载依赖包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层流错误（Curl error 92）。其中 cmake-data 和 git-core 在重试后成功下载，但 gcc-c++（约 13MB）两次下载尝试均失败，DNF 耗尽镜像列表后构建终止。这是基础设施/网络层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 中 `dnf install` 命令语法和包名均正确——DNF 已成功解析出 258 个待安装包的依赖关系（见日志 `Dependencies resolved.` 阶段）。失败发生在第二阶段的"实际下载 RPM 包"过程中，原因是 openEuler 24.03-LTS-SP4 OS 仓库的 HTTP/2 传输不稳定。该问题具有随机性：同一批构建中其他包（gcc、cmake 本体等）均成功下载，仅 gcc-c++ 失败；前序的其他 PR 构建同样依赖该仓库却未触发此错误。

## 修复方向

### 方向 1（置信度: 高）
**直接重试 CI 构建。** 此失败是由 openEuler 24.03-LTS-SP4 RPM 仓库镜像的瞬时网络波动导致 HTTP/2 流异常中断。Dockerfile 本身无需修改。重新触发 CI build（rerun）大概率可通过，因为 cmake-data 和 git-core 在同一次构建中重试后也已成功下载。

### 方向 2（置信度: 低）
**在 Dockerfile 中添加 DNF 重试配置。** 若此问题频繁复现，可考虑在 `dnf install` 命令前增加重试参数（如设置 `retries=10` 的 dnf 全局配置），使 DNF 在遇到 HTTP/2 流错误时自动多次重试。但此改动超出本次 PR 的范围，且同类仓库其他 Dockerfile 亦无此模式，不建议主动采用。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 OS 仓库镜像（`repo.****.org`）在 CI 构建时段是否有已知的网络波动或维护窗口。
- 若重试后仍失败，排查 CI runner 所在网络到该镜像站的路由质量问题（丢包、MTU 等可能导致 HTTP/2 帧异常）。
- 确认是否只有 x86_64 架构的该镜像出现问题（日志中仅显示 x86-64 runner），aarch64 构建节点是否遇到同样问题。

## 修复验证要求
无需 code-fixer 介入。Code Fixer 无需处理此 infra-error 类型的失败。
