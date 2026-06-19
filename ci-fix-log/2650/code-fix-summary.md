# 修复摘要

## 修复的问题
Dockerfile 中 `TORCH_VERSION=2.12.0` 与 torchvision 0.27.1 的上游依赖 `torch==2.12.1` 不兼容，导致 pip 依赖解析失败。

## 修改的文件
- `AI/torchvision/0.27.1/24.03-lts-sp3/Dockerfile`: 将 `ARG TORCH_VERSION=2.12.0` 修正为 `ARG TORCH_VERSION=2.12.1`

## 修复逻辑
CI 日志显示 `torchvision 0.27.1+cpu depends on torch==2.12.1`，而 Dockerfile 中硬编码了 `ARG TORCH_VERSION=2.12.0`，pip 无法同时满足这两个约束导致 `ResolutionImpossible` 错误。已从上游 `https://download.pytorch.org/whl/cpu/` 验证 `torch==2.12.1` 和 `torchvision==0.27.1+cpu` 均存在于该索引中，将 TORCH_VERSION 改为 2.12.1 即可解决版本冲突。

## 潜在风险
无