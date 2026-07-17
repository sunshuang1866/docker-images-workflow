# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（`infra-error`）：CI Runner 上缺少 `shunit2` Shell 测试框架依赖，导致镜像构建完成后的 `[Check]` 阶段无法执行容器功能测试脚本。

## 修改的文件
无。PR 涉及的 4 个文件均无需修改。

## 修复逻辑
根据 CI 失败分析报告，此失败与 PR 代码变更无关：
- Docker 镜像构建阶段（`[Build]`）完全成功，PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上从源码编译、安装、镜像导出及推送均无误。
- 失败仅发生在构建完成后的 `[Check]` 测试阶段，根因是 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本（第 13 行）在 `source shunit2` 时找不到该工具。
- 修复方向：在 CI Runner 上安装 `shunit2`（如 `dnf install shunit2`），属于 CI 基础设施配置变更，不涉及仓库代码修改。

## 潜在风险
无