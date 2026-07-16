# 修复摘要

## 修复的问题
CI 基础设施问题：CI runner（`ecs-build-docker-aarch64-01-sp`）缺少 `shunit2` shell 测试框架依赖，导致镜像构建成功后的 `[Check]` 验证阶段失败。与 PR 代码无关，无需代码修改。

## 修改的文件
无（infra-error，非代码问题）

## 修复逻辑
- 失败发生在 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`，报错 `shunit2: No such file or directory`
- Docker 镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 已成功构建并推送，所有构建步骤（下载 Go → 解压 → 修复时间戳 → 清理构建工具 → 推送）均已完成
- PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及元数据文件，与 `shunit2` 缺失无关
- `shunit2` 是 eulerpublisher 测试框架的运行时依赖，属于 CI 基础设施问题，需由基础设施团队在 CI runner 上安装 `shunit2`（如 `dnf install shunit2`）

## 潜在风险
无