# 修复摘要

## 修复的问题
CI 基础设施故障：BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 阶段被异常终止（`graceful_stop`），导致 gRPC 连接断开（`EOF`），构建器随后不可用（`no builder found`）。此为 infra-error，与 PR 代码变更无关。

## 修改的文件
- 无代码修改。

## 修复逻辑
CI 失败分析报告将此失败定性为 **infra-error**（置信度：高）。错误发生在 Docker 构建步骤 `#7 [2/4]` 的 `dnf install` 阶段，即 BuildKit 守护进程/构建器实例意外退出导致的 gRPC 传输层错误。PR 变更仅为新增标准的 scann 1.4.2 Dockerfile（含 dnf 安装编译工具链、编译安装 Python 3.9.19、pip 安装 scann）、README 和 meta.yml 条目更新，Dockerfile 内容无语法或逻辑问题。根据修复原则中的"如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"，本次无需修改任何代码文件。

## 潜在风险
无。建议直接重新触发 CI 构建（retry），大概率在下一次构建中通过。