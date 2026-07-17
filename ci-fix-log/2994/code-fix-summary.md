# 修复摘要

## 修复的问题
无需代码修改。CI 失败是基础设施问题（BuildKit builder 在 Docker 构建过程中被优雅终止），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 Docker build 阶段 `#7 [2/4]`（`dnf install` 下载元数据时），BuildKit builder 实例 `euler_builder_20260709_224657` 被优雅终止（`graceful_stop`），导致客户端连接断开（`rpc error: code = Unavailable desc = closing transport`）。PR 新增的 Dockerfile 语法正确、依赖声明完整，且同目录下 sp3 版本镜像 CI 历史无类似问题。此错误属于 CI 基础设施的偶发性 Builder 失联，重新触发 CI 流水线即可恢复。

## 潜在风险
无