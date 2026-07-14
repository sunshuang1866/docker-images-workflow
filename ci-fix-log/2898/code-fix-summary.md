# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：CI runner 上缺少 `shunit2` 测试框架，导致后置检查阶段的 `common_funs.sh` 脚本执行失败。Docker 镜像构建和推送均成功完成。

## 修改的文件
无需代码修改。

## 修复逻辑
根据 CI 分析报告，失败类型为 `infra-error`，根因是 CI runner 环境缺少 `shunit2` 测试框架（`common_funs.sh:13: shunit2: No such file or directory`），与 PR #2898 的代码变更无关。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Docker 构建和镜像推送均成功。此问题需由 CI 基础设施团队在 runner 上安装 `shunit2` 解决，PR 代码本身无需任何修改。

## 潜在风险
无