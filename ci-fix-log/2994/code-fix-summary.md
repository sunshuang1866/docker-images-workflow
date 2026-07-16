# 修复摘要

## 修复的问题
无需修复代码。CI 失败为基础设施问题（infra-error），BuildKit 构建器 `euler_builder_20260709_224657` 在 Docker 镜像构建到第 2/4 步（dnf install 下载仓库元数据期间）被优雅关闭（graceful_stop），随后构建器实例被移除，导致构建中断。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认该失败与 PR 代码变更完全无关。PR 变更仅为新增 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 语法正确，构建步骤合理。失败发生在 BuildKit 基础设施层面（构建器在构建过程中被提前回收），任何 Dockerfile 在此环境下均可能触发同类失败。

建议操作：重新触发 CI 运行（retry）。若多次重试后仍反复出现同一错误，需排查 CI 节点 `ecs-build-docker-x86-hk` 上 BuildKit builder 的资源配额、超时配置或节点健康状态。

## 潜在风险
无