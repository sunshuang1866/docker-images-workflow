# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error：BuildKit builder 实例在执行 `dnf install` 过程中被外部因素主动终止（`graceful_stop`），导致 gRPC 连接断开。

## 修改的文件
无代码变更。

## 修复逻辑
CI 分析报告已明确判断该失败为 **infra-error**，与 PR 代码变更无关。失败发生在 Docker 构建步骤 `#7 [2/4] RUN dnf install -y ...`，原因是 BuildKit builder 守护进程被环境/系统终止（GOAWAY 帧 `debug data: "graceful_stop"`），而非 Dockerfile 本身有语法或逻辑错误。PR 新增的 Dockerfile 结构正确，所有文件（Dockerfile、README.md、image-info.yml、meta.yml）内容一致，无需修改。

## 潜在风险
无。建议触发 CI 重试（rerun the failed job），大概率能通过。若重试后仍持续失败，需排查 CI 基础设施侧 BuildKit 守护进程状态或资源限制。