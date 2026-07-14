# 修复摘要

## 修复的问题
CI 基础设施问题（`infra-error`）——CI 运行环境缺少 `shunit2` Shell 测试框架，错误发生在 `[Check]` 阶段加载 `common_funs.sh` 时，与 PR 代码变更无关。

## 修改的文件
无（无需修改任何代码文件）

## 修复逻辑
此次失败为 `infra-error`：
- Docker 镜像构建和推送均成功完成
- 失败发生在构建完成后的 `[Check]` 阶段，`common_funs.sh:13` 尝试 `source shunit2` 但该工具未安装在 CI aarch64 构建节点上
- PR 变更内容（Dockerfile、README.md、image-info.yml、meta.yml）均为声明式配置，不涉及 CI 测试框架的运行时依赖
- 修复应由 CI 基础设施管理员在构建节点上安装 `shunit2` 包（如 `yum install shunit2`），然后重新触发构建

## 潜在风险
无