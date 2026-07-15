# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 **infra-error**，由 openEuler 24.03-LTS-SP4 RPM 仓库镜像的 HTTP/2 协议层服务端故障引起。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出此失败与 PR 变更无关，Dockerfile 中的 `dnf install` 命令语法正确、包名均有效。失败根因是 `repo.****.org` 仓库镜像服务端存在 HTTP/2 协议层 bug（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR`），导致大体积 RPM 包（如 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 34 MB）下载失败。这是 CI 基础设施层面的临时性问题，属于 infra-error，无需修改任何代码。直接触发 CI 重跑即可。如果重跑后仍然失败，需联系 openEuler 仓库镜像运维团队排查 HTTP/2 服务端问题。

## 潜在风险
无