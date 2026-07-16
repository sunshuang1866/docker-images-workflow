# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），与 PR #2995 的代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败发生在 `[Check]` 阶段，由 `eulerpublisher` 测试框架中的 `bwa_test.sh` 脚本使用 Windows 风格的 CRLF 换行（`\r\n`）导致 shebang 行变为 `#!/bin/sh\r`，Linux 内核找不到解释器 `/bin/sh\r`，触发 `bad interpreter: No such file or directory` 错误。

该 PR 仅新增了 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件，Docker 镜像构建阶段完全成功。失败根因在 CI 基础设施（`eulerpublisher` 包），需由 CI 维护者修复，不属于本 PR 代码层面可解决的问题。

## 潜在风险
无