# 修复摘要

## 修复的问题
在 openEuler 24.03-LTS-SP4 的 glibc 2.42 Dockerfile 中补充缺失的构建依赖 `gawk`（GNU awk）。

## 修改的文件
- `Others/glibc/2.42/24.03-lts-sp4/Dockerfile`: 在 `dnf install` 命令中添加 `gawk` 包

## 修复逻辑
对比已有且正常构建的 SP1/SP2 Dockerfile，三者 `dnf install` 列表完全一致（仅 ARG BASE 不同），说明 Dockerfile 结构本身没有问题。根据 glibc 2.42 官方 INSTALL 文档（已从上游 `bminor/glibc` 仓库 `glibc-2.42` tag 获取验证），glibc 明确要求 GNU awk 3.1.2+（`gawk`），其 `configure` 脚本会检测 `gawk` 是否可用。SP1/SP2 基础镜像可能预装了 `gawk`，而 SP4 基础镜像未预装，导致配置阶段失败。此次修复仅添加 `gawk` 这一确认的硬性依赖，与 CI 分析报告方向 1 一致。

由于 CI 日志缺失，分析报告置信度为"低"。本次修复采用了最保守、最可论证的方案：仅添加 glibc INSTALL 文档明确列为必选工具的 `gawk`，不添加未确认的包（如 `gettext-devel`、`kernel-headers`）。

## 潜在风险
无。`gawk` 是 glibc 构建的硬性依赖，添加后不会影响其他功能。若构建仍失败，需获取实际 CI 日志进一步排查。