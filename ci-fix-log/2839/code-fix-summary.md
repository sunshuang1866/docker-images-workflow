# 修复摘要

## 修复的问题
CI 基础设施问题，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因是 CI runner 缺少 `shunit2` shell 测试框架，导致 `common_funs.sh` 在 [Check] 阶段无法找到 `shunit2` 命令。

该 PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，以及更新 README.md 和 meta.yml。Docker 镜像的构建（#8 DONE 268.4s）和推送（[Push] finished）均已成功完成。失败发生在构建和推送全部成功之后的 [Check] 测试阶段，与 PR 代码变更完全无关。

此问题需要在 CI runner 环境中安装 `shunit2`，或由 CI 基础设施团队调整测试脚本来自动获取该依赖。Code Fixer 不应修改任何源代码。

## 潜在风险
无 — 未对任何源文件进行修改。