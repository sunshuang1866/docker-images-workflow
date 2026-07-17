# 修复摘要

## 修复的问题
无代码修复。CI 失败原因为 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 DNF 包安装阶段被优雅终止（GOAWAY 帧 `graceful_stop`），属于 CI 基础设施故障，与 PR 代码变更无关。

## 修改的文件
无修改。所有 PR 文件（Dockerfile、README.md、image-info.yml、meta.yml）均无问题，无需任何代码改动。

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，置信度"高"。构建在进行到 DNF 下载元数据阶段（约 39 秒）时，BuildKit builder 被外部机制关闭（可能是节点资源不足、缩容、或容器存活时间限制）。PR 仅新增了标准的基础编译工具安装命令（与仓库中数百个其他 Dockerfile 使用相同的 `dnf install` 模式），不存在语法或逻辑错误。

**修复方向**：重新触发 CI 构建流水线。若重试后仍失败，需由 CI 运维团队排查 `euler_builder_*` 实例所在节点的资源状况。

## 潜在风险
无。未修改任何代码，不引入任何风险。