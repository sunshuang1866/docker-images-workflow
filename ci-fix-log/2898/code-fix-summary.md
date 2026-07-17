# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：CI runner 环境缺少 `shunit2` Shell 测试框架依赖。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此失败为 **infra-error**，与 PR 代码变更无关：

1. Docker 镜像构建（`[Build]`）和推送（`[Push]`）均已成功完成，PR 新增的 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile` 及相关元数据文件没有问题。
2. 失败仅发生在构建后的 `[Check]` 阶段，根因是 CI runner（`ecs-build-docker-aarch64-01-sp`）上的 `common_funs.sh` 脚本在第 13 行引用 `shunit2`，但 `shunit2` 未安装在 CI 节点上。
3. 解决方法：在 CI runner 上执行 `dnf install shunit2 -y` 安装该包，然后重新触发 CI 构建即可。

根据任务指令，`infra-error` 类型的失败无需修改任何源代码。

## 潜在风险
无。不涉及代码变更。