# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在通过 HTTP/2 协议传输过程中出现流中断（Curl error 92: INTERNAL_ERROR），导致多个包下载失败。其中 `cmake-data` 和 `git-core` 经重试后成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 两次重试（stream 65、stream 83）均失败，最终 dnf 耗尽所有镜像尝试后放弃。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个 Grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关文档/元数据更新。Dockerfile 自身语法和 `dnf install` 包列表均正确——依赖解析阶段（`Dependencies resolved`）已成功完成，258 个包均已识别，失败仅发生在后续的实际下载阶段。此错误是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端临时性不稳所致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 重新构建。** 由于根因是 RPM 仓库镜像 HTTP/2 协议层临时性故障，属于瞬态网络问题，无需任何代码修改。在 PR 上重新触发 CI 流水线（如 `/retest` 或在 Jenkins 中重新构建）即可。若多次重试均失败，则需排查 openEuler 24.03-LTS-SP4 仓库镜像的服务健康状态。

### 方向 2（置信度: 低）
若问题持续复现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 或 `--setopt=timeout=30` 增加下载重试容忍度。但此方案是绕过而非修复根因，仅作为镜像持续不稳定的临时变通。

## 需要进一步确认的点
1. 确认此次构建失败在同一时间段内是否其他 PR 也遇到了相同的 `Curl error (92)`——如果是，说明是 openEuler 24.03-LTS-SP4 仓库镜像的普遍性问题。
2. 确认 aarch64 架构的构建结果——日志仅包含 x86_64 的构建过程，若 aarch64 也失败，需检查其日志是否指向同一类网络问题。
