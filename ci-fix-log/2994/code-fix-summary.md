# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS 元数据时意外终止（`graceful_stop` goaway 帧），导致 gRPC 连接断开。

## 修改的文件
无

## 修复逻辑
分析报告确认此 CI 失败与 PR 变更无关。PR 仅新增了 scann 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 语法正确，不存在导致构构建器崩溃的逻辑。失败发生在 `dnf install` 下载阶段（速率仅 77 kB/s），构建器在客户端侧发送 `graceful_stop` 后关闭连接，属于 CI runner 资源不足或网络瞬断导致的基础设施问题。建议直接重新触发 CI 构建。

## 潜在风险
无