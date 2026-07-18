# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（BuildKit 构建器实例 `euler_builder_20260709_224657` 被服务端主动终止），与 PR 代码无关。

## 修改的文件
无。所有 PR 改动的文件（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`、`Others/scann/README.md`、`Others/scann/doc/image-info.yml`、`Others/scann/meta.yml`）内容正常，无需修改。

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，置信度高。直接错误为 `rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"`，随后 `no builder "euler_builder_20260709_224657" found`。这是 BuildKit 构建器在 `dnf install` 下载元数据阶段被 CI 基础设施服务端主动关闭，与本次 PR 的 Dockerfile 内容无关。建议直接触发 CI 重试（如重新 push 或 `/retest`）即可通过。

## 潜在风险
无