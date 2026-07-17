# 修复摘要

## 修复的问题
无需代码修改。此失败为 **infra-error**（CI 基础设施问题），非 PR 代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`，置信度：中
- 直接错误：CI runner 上 `eulerpublisher` 包内置的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 换行符（CRLF），shebang 行 `#!/bin/sh` 末尾附带了回车符 `\r`（日志中显示为 `^M`），导致 `/bin/sh^M` 被当作解释器路径，触发 `bad interpreter: No such file or directory`
- 与 PR 变更无关：Docker 镜像构建完全成功（`[Build] finished`、`[Push] finished`），编译和推送均无错误。失败仅发生在 CI runner 内置的 `eulerpublisher` 测试脚本执行阶段
- PR 的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）内容正确，无代码缺陷

**根因是 CI 基础设施中的 `bwa_test.sh` 脚本换行符问题**，应由 CI 维护者通过 `dos2unix` 或 `sed -i 's/\r$//'` 修复，不属于本次 PR 的代码修改范围。

## 潜在风险
无