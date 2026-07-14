# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error）：CI runner 环境中缺少 `shunit2` Shell 测试框架。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- Docker 镜像构建（meson setup/compile/install）全部 422/422 个编译目标通过
- Docker 镜像导出和推送均成功完成
- 失败发生在 CI 流水线的 [Check] 阶段，`eulerpublisher` 测试脚本的 `common_funs.sh` 调用 `. shunit2` 时找不到该框架
- 根因与 PR 变更无关——PR 仅新增 bind9 Dockerfile、配置文件和文档条目

此为 CI 基础设施维护工作，需在 CI runner 环境中安装 `shunit2`（如 `dnf install shunit2`），而非修改 PR 代码。

## 潜在风险
无