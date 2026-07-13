# 修复摘要

## 修复的问题
为 `meta.yml` 中新增的 `chatglm2_6b-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2403sp4` 条目添加 `arch: aarch64` 约束，避免 CI 将仅支持 arm64 的镜像调度到 x86_64 构建节点。

## 修改的文件
- `AI/llm/meta.yml`: 在新增的 `oe2403sp4` 条目中添加 `arch: aarch64` 行

## 修复逻辑
新增的 Dockerfile 以 `fastchat-pytorch2.1.0.a1-cann7.0.RC1.alpha002-oe2203sp2` 为基础镜像，该镜像仅发布 `linux/arm64` 版本。CI 调度器在无 `arch` 约束的情况下将该构建分配到 x86_64 节点（`ecs-build-docker-x86-hk`），导致拉取 arm64 镜像后 `/bin/sh` 因架构不匹配而报 `exec format error`。添加 `arch: aarch64` 后，CI 会将此构建限制在 aarch64 节点上执行，与 repo 中其他仅 arm64 的镜像（如 `AI/pytorch`、`AI/euler-copilot-fast-inference-qwen` 等）的处理方式一致。

## 潜在风险
无。此为架构约束声明，不影响镜像内容或构建行为，仅限制 CI 调度目标节点。