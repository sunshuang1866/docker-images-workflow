# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error），BuildKit 构建器在 `dnf install` 下载元数据时被优雅终止（graceful_stop/GOAWAY），与 Dockerfile 内容无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：失败发生在 `RUN dnf install` 执行期间（进度约 38%），根因是 BuildKit 构建器 `euler_builder_20260709_224657` 被基础设施侧终止（graceful stop），导致 gRPC 连接断开。该 PR 新增的 Dockerfile 内容语法正确，安装的均为 openEuler 仓库中的常规构建依赖，不存在导致构建器崩溃的代码缺陷。此问题与 PR 代码变更无关，无需修改任何源代码文件。

**建议操作**：重新触发 CI 构建。若多次重试均在同一位置失败，需排查 CI runner（`ecs-build-docker-x86-hk`）的资源状况（内存、磁盘空间、并发构建数上限）。

## 潜在风险
无