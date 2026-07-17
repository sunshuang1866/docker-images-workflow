# 修复摘要

## 修复的问题
CI 基础设施异常（infra-error），无需修改 PR 代码。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告确认该失败为 **infra-error**：Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被上层 CI 基础设施优雅终止（goaway frame 携带 `graceful_stop` 指令），导致 gRPC 传输连接断开。构建中断发生在 dnf 元数据下载阶段（`[2/4] RUN dnf install`），此时尚未进入实际包安装流程，Dockerfile 语法和内容均无错误。

PR 新增的 Dockerfile 内容正确，`dnf install` 包列表均为 openEuler 24.03-LTS-SP4 标准仓库下的有效包名。README.md、image-info.yml、meta.yml 均无问题。

**建议操作**：重新触发 CI 构建（re-run / re-trigger）即可。若反复出现同类问题，需排查 CI 调度器对 `euler_builder_*` 构建器的生命周期管理是否异常。

## 潜在风险
无。未修改任何代码。