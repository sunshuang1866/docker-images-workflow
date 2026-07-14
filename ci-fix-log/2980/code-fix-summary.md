# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 软件仓库镜像在 HTTP/2 传输层反复出现流错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等 RPM 包下载失败，构建中断。无需代码修改。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，该失败属于 **infra-error**，根因是 openEuler 仓库镜像服务器（`repo.****.org`）的 HTTP/2 协议层不稳定性，导致大文件（如 `gcc-c++` 13MB）下载时流被异常关闭。这与 PR #2980 新增的 Dockerfile 内容无关——Dockerfile 中的 `dnf install` 命令格式与同类镜像完全一致，语法正确。按照修复规范，infra-error 不应通过修改代码来解决。建议等待仓库镜像恢复后重试 CI，或联系 openEuler 基础设施团队排查 HTTP/2 服务稳定性。

## 潜在风险
无