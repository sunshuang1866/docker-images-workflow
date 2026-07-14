# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：构建环境无法连接 `archive.apache.org`（TCP 连接超时），与 PR 代码逻辑无关。

## 修改的文件
无

## 修复逻辑
1. 失败类型确认为 `infra-error`，CI 构建环境到 `archive.apache.org` 的网络不可达导致 wget 下载 Spark 3.4.2 失败。
2. 验证了替代下载源：
   - `dlcdn.apache.org/dist/spark/spark-3.4.2/` → **404**（CDN 不保留旧版本）
   - `downloads.apache.org/dist/spark/spark-3.4.2/` → **404**（主下载站仅保留 3.5.8+ 版本）
   - `archive.apache.org` → 文件存在（已确认目录列表），但 CI 网络不可达
3. 该 Dockerfile 使用的 `archive.apache.org` 是项目通用模式：全仓库 34 处 Spark 下载（包括所有 Kyuubi 版本和 Spark 自身 Dockerfile）均使用同一域名，此 Dockerfile 与项目规范一致。
4. 根据修复规则："如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"。

## 潜在风险
无。此为 CI 基础设施网络波动问题，建议重试构建。若问题持续出现，需排查 CI 环境到 `archive.apache.org`（65.108.204.189）的网络路由。