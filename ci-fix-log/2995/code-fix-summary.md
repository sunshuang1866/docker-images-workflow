# 修复摘要

## 修复的问题
无需代码修改。CI 失败是基础设施问题（infra-error），由 eulerpublisher CI 工具包内置的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF）导致，与 PR #2995 提交的代码变更无关。

## 修改的文件
无。PR 涉及的所有文件（Dockerfile、README.md、image-info.yml、meta.yml）均无问题，无需修改。

## 修复逻辑
- **失败原因**：eulerpublisher CI 工具在 [Check] 阶段执行 `bwa_test.sh` 时，shebang 行 `#!/bin/sh` 末尾附带了 `\r` 字符（CRLF），导致内核查找 `/bin/sh\r` 失败，报 `bad interpreter: No such file or directory`。
- **与 PR 的关系**：该 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新元数据文件，镜像构建和推送均成功。[Check] 阶段的失败源于上游 eulerpublisher 包中的测试脚本自身存在 CRLF 污染，不属于本仓库代码问题。
- **修复方向**：应在上游 eulerpublisher 仓库中对 `tests/container/app/bwa_test.sh` 执行换行符转换（`dos2unix` 或 `sed -i 's/\r$//'`），并排查同一目录下其他测试脚本是否存在相同的 CRLF 问题。

## 潜在风险
无。未对源码仓库做任何代码修改。