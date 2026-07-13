# 修复摘要

## 修复的问题
`meta.yml` 中新增的 `2024.2.0-oe2403sp4` 条目缺少 `arch: x86_64` 约束，导致 CI 将该镜像调度到 aarch64 runner 上构建失败。

## 修改的文件
- `AI/oneapi-basekit/meta.yml`: 为 `2024.2.0-oe2403sp4` 条目补充 `arch: x86_64` 字段

## 修复逻辑
CI 分析报告指出，`2024.2.0-oe2403sp4` 条目未指定 `arch` 字段，导致 CI 调度器将其同时派发到 x86_64 和 aarch64 runner。而 Intel oneAPI Basekit 的 RPM 仓库仅提供 x86_64 架构的包，aarch64 runner 上报 `does not have a compatible architecture` 错误。已有的 `2024.2.0-oe2403lts` 条目明确设置了 `arch: x86_64`，新条目需保持一致，使 CI 仅调度 x86_64 runner 构建该镜像。

## 潜在风险
无