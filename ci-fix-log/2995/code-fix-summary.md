# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error，根因是 CI 框架 `eulerpublisher` 内置测试脚本 `bwa_test.sh` 存在 CRLF 换行符问题，与本次 PR 的 Dockerfile/元数据变更无关。

## 修改的文件
无

## 修复逻辑
分析报告明确指出：
- 失败发生在 CI 框架 `eulerpublisher` 的 `[Check]` 阶段，其内置脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的 shebang 行末尾带有 `\r`（`^M`），导致系统查找名为 `/bin/sh\r` 的解释器失败。
- PR 仅新增 Dockerfile 和更新元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像的构建和推送均已成功。
- 该问题需要 CI 基础设施维护者对 `eulerpublisher` 包中的 `bwa_test.sh` 执行 `dos2unix` 或等效操作清除 CRLF 字符。
- 与 PR 代码无关，PR 的 Dockerfile 无需任何修改。

## 潜在风险
无