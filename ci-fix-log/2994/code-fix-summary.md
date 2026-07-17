# 修复摘要

## 修复的问题
CI 基础设施故障（构建器实例异常终止），与 PR 代码无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出本次失败为 **infra-error**，置信度**高**。直接错误为 `ERROR: no builder "euler_builder_20260709_224657" found`，根因是 CI 使用的 BuildKit 构建器实例在 `dnf install` 下载软件包阶段被意外终止（`graceful_stop`），导致 RPC 连接中断。

该 PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → 编译 Python 3.9 → pip 安装 scann）及配套的 README.md、image-info.yml、meta.yml，所有变更均遵循项目既有模板，不包含任何可能触发构建器崩溃的非标准操作。

**修复方向：触发 CI 重试即可。** 这是典型的构建基础设施短暂故障（runner 上的 buildkit 守护进程被重启、资源不足导致构建器被驱逐、或网络抖动导致 RPC 连接断开），重新触发 CI 流水线大概率通过。

## 潜在风险
无