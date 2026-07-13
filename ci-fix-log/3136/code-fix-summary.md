# 修复摘要

## 修复的问题
新增的 `2024.2.0-oe2403sp4` 镜像条目缺少 `arch: x86_64` 架构限制，导致 CI 在 aarch64 节点上也尝试构建该镜像，Intel oneAPI 包仅支持 x86_64 而安装失败。

## 修改的文件
- `AI/oneapi-runtime/meta.yml`: 为 `2024.2.0-oe2403sp4` 条目添加 `arch: x86_64`，与已有的 `2024.2.0-oe2403lts` 条目保持一致。

## 修复逻辑
CI 分析报告明确指出：`meta.yml` 中新增的 `2024.2.0-oe2403sp4` 条目缺少 `arch: x86_64` 字段，而 Intel oneAPI 仓库仅提供 x86_64 架构的 RPM 包。CI 构建运行在 aarch64 节点上时，由于未限制架构，yum 尝试安装 x86_64 包导致 "does not have a compatible architecture" 错误。参照同文件中 `2024.2.0-oe2403lts` 条目的写法，添加 `arch: x86_64` 使 CI 仅对 x86_64 架构构建该镜像。

## 潜在风险
无