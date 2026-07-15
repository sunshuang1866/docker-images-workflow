# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施问题（BuildKit builder 意外终止），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告将该问题定性为 `infra-error`。失败原因是 Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被 `graceful_stop` 终止，导致 API 连接断开（EOF）。这是 CI runner 节点（`ecs-build-docker-x86-hk`）侧的 BuildKit daemon 被资源回收、节点调度异常或空闲超时所触发，属于 CI 基础设施层面的问题，与 PR #2994 新增的 Dockerfile 内容无关。

PR 新增的 Dockerfile（安装编译工具链 → 编译 Python 3.9.19 → pip 安装 scann）逻辑正确，参考了同类镜像 `scann 1.4.2 on 24.03-lts-sp3` 的构建方式，无需做任何代码修改。

建议重新触发 CI 构建，大概率可恢复正常。

## 潜在风险
无