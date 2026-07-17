# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），CI Runner 环境缺少 `shunit2` 框架，导致 `common_funs.sh` 脚本在 [Check] 阶段执行失败。与本次 PR 的代码变更无关。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
本次 PR 仅新增 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 镜像的构建（[Build]）和推送（[Push]）步骤已全部成功完成。失败仅发生在构建后的 [Check] 阶段，由 CI Runner 上缺失 `shunit2` 包导致。此为 CI 基础设施配置问题，需由 CI 管理员在 Runner 环境/基础镜像中安装 `shunit2`（如 `dnf install shunit2 -y`），无需修改本 PR 的任何源代码。

## 潜在风险
无