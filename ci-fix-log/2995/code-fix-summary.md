# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），根因是 eulerpublisher CI 工具链中的测试脚本 `bwa_test.sh` 包含 Windows 风格 CRLF 换行符，导致 shebang 行末尾携带不可见回车符 `\r`，内核无法找到 `/bin/sh\r` 解释器。

## 修改的文件
无。PR 变更的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均与此次失败无关，Docker 镜像构建阶段已完全成功。

## 修复逻辑
分析报告明确指出：
- 失败发生在镜像构建成功之后的 `[Check]` 阶段，由 eulerpublisher 预置的 `bwa_test.sh` 脚本的 CRLF 换行符缺陷导致
- 该缺陷在 PR 提交前已存在于 eulerpublisher 仓库中，本次 PR 仅是触发了该脚本被执行
- 修复应由 eulerpublisher 仓库维护者执行（使用 `dos2unix` 转换或通过 `.gitattributes` 强制 LF）

## 潜在风险
无。本次 PR 代码无任何问题，无需修改。