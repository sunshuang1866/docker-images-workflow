# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（BuildKit builder 被服务端 graceful_stop 导致连接中断），与 PR 代码变更无关。

## 修改的文件
无（infra-error，无需修改任何文件）

## 修复逻辑
CI 分析报告明确指出该失败为 `infra-error`：
- BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 Docker 构建步骤 `[2/4] RUN dnf install` 时被服务端主动终止（`graceful_stop`）
- 构建仅进行到 `dnf` 下载元数据阶段（约 39 秒），远未执行到 `pip install scann` 等应用特有逻辑
- 日志中 `graceful_stop` 和 `NO_ERROR` 表明 builder 端为主动、无错误的关闭，属于基础设施生命周期管理范畴
- CI 预检阶段全部通过，未报告任何 PR 代码层面的错误
- 重新触发 CI 构建即可，无需修改任何代码

## 潜在风险
无