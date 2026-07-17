# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 `infra-error`：openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 运行时出现 HTTP/2 协议层故障，导致 `dnf install` 下载 RPM 包时持续遭遇 Curl error (92): HTTP/2 stream INTERNAL_ERROR，最终多个包（gcc、gcc-gfortran、guile、glibc-devel 等）下载失败。

## 修改的文件
无。此失败与 PR #2992 的代码变更无关，Dockerfile 语法正确，`dnf install` 命令写法与同项目其他 Dockerfile 一致。

## 修复逻辑
根据 CI 失败分析报告，此失败被定性为 `infra-error`（置信度：高），属于 CI 基础设施/镜像仓库侧的暂时性故障，而非代码问题。证据包括：
1. 两个独立构建阶段（builder 和 runtime）同时遭遇相同的 Curl error (92)，表明是仓库侧普遍问题
2. 受影响的包横跨多个不同 RPM（gcc、gcc-gfortran、guile、glibc-devel），排除个别包损坏可能
3. `No more mirrors to try` 表明 dnf 已尝试所有可用镜像，均失败

**推荐操作**：通过 CI 平台重新触发构建（retry）。若多次重试均失败，需排查 CI 构建环境到仓库镜像站的网络链路中是否有 HTTP/2 不兼容的中间设备。

## 潜在风险
无（未修改任何代码）。