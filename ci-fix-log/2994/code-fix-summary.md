# 修复摘要

## 修复的问题
无需修改代码。CI 失败属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 Docker BuildKit 构建器执行 `dnf install` 下载 openEuler 包仓库元数据阶段（仅下载了 2.8 MB 元数据，速度 77 kB/s，耗时约 37 秒），构建器收到 `graceful_stop` 信号后被终止。此时构建尚未进入 PR 新增的 scann 任何定制逻辑（Python 编译、scann pip 安装），失败步骤是通用基础系统包安装步骤。

- `graceful_stop` 和 `NO_ERROR` 表明 BuildKit daemon 被外部因素干净关闭（非代码崩溃）
- 根因可能为 CI runner 资源不足（OOM/磁盘）、job 超时策略或基础设施节点管理动作
- PR 新增的所有文件（Dockerfile、README.md、image-info.yml、meta.yml）无语法或逻辑问题

**建议操作**：在 CI 系统中重新触发该 job（retry），观察是否可复现；若反复失败，检查 CI runner 节点的资源情况。

## 潜在风险
无（未修改任何代码）