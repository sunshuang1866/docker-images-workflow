# 修复摘要

## 修复的问题
无需代码修复。本次 CI 失败为 BuildKit 基础设施瞬时故障（构建器容器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据期间被优雅终止），与 PR 代码变更无关。

## 修改的文件
无。所有 PR 文件（Dockerfile、README.md、image-info.yml、meta.yml）无需修改。

## 修复逻辑
CI 分析报告明确结论为 infra-error，错误特征为 `graceful_stop` / `closing transport` / `no builder found`，这是 CI runner 侧 BuildKit 构建器容器因资源压力或调度策略被意外回收导致的一次性基础设施问题。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的构建定义文件，Dockerfile 内容无语法或逻辑错误。重新触发 CI 构建即可验证。

## 潜在风险
无