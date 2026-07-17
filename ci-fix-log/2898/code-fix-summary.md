# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：aarch64 CI runner 的 `eulerpublisher` 环境中缺少 `shunit2` shell 测试框架。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`，置信度 **高**。PR 仅新增了标准 Go Dockerfile（`Others/go/1.25.6/24.03-lts-sp4/Dockerfile`）及配套元数据更新。Docker 镜像构建和推送均已成功完成（`[Build] finished`、`[Push] finished`），镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 已正确推送到 registry。

失败发生在 `[Check]` 验证测试阶段，原因是 CI aarch64 测试节点的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 脚本无法 source `shunit2`（`shunit2: No such file or directory`）。`shunit2` 是 CI runner 测试环境中的工具依赖，不是容器镜像内容的一部分。PR 的代码变更完全正确，不会影响 CI runner 上的软件安装状态。

**与 PR 变更无关，无需修改源代码。** 需要 CI 环境管理员在 aarch64 测试节点的 `eulerpublisher` 环境中安装 `shunit2` shell 测试框架。

## 潜在风险
无