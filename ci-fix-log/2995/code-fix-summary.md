# 修复摘要

## 修复的问题
无代码修复。CI 失败属于基础设施问题（infra-error），根因在 CI 工具链 `eulerpublisher` 内置的 `bwa_test.sh` 脚本使用了 CRLF 行尾，与 PR 提交的代码变更无关。

## 修改的文件
无。PR 代码无需修改。

## 修复逻辑
1. CI 构建（`#7 DONE 199.0s`）和镜像推送（`[Push] finished`）均完全成功。
2. 失败发生在构建成功后的 `[Check]` 阶段，错误为 `/bin/sh^M: bad interpreter`，表明 `eulerpublisher` 工具包中的 `tests/container/app/bwa_test.sh` 脚本行尾编码为 CRLF（Windows 风格），导致 shebang `#!/bin/sh` 被错误解析。
3. 此问题源于 CI 基础设施（`eulerpublisher` 工具代码仓库或 PyPI 包），与 PR #2995 新增的 `HPC/bwa/0.7.18/24.03-lts-sp4/` 目录下的 Dockerfile、README、image-info.yml、meta.yml 文件无任何关联。
4. 无需对 PR 代码做任何修改。

## 潜在风险
无。此修复为空操作，不涉及任何代码变更。CI 基础设施维护者需修复 `eulerpublisher` 仓库中 `bwa_test.sh` 的 CRLF 行尾问题（`dos2unix` 或 `sed -i 's/\r$//'`）。