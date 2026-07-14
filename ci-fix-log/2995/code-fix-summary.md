# 修复摘要

## 修复的问题
CI 基础设施故障：`eulerpublisher` 包内置的 `bwa_test.sh` 测试脚本包含 Windows 风格 CRLF 行尾，导致 shebang 解析失败（`/bin/sh^M: bad interpreter`），与 PR 代码变更完全无关。

## 修改的文件
无代码修改（infra-error，无需修改 PR 代码文件）

## 修复逻辑
CI 分析报告明确指出此失败为 `infra-error`，根因是 CI 工具 `eulerpublisher` 的内置测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 CRLF 行尾。该文件不属于 PR 变更范围，也不是本仓库中的文件。Docker 镜像构建（编译、导出、推送）均已成功完成，PR #2995 的 Dockerfile 和其他代码变更本身无问题。

此问题需由 CI 维护者修复 `eulerpublisher` 包，将测试脚本的行尾从 CRLF 转换为 LF，例如：
```bash
sed -i 's/\r$//' /etc/eulerpublisher/tests/container/app/bwa_test.sh
```

## 潜在风险
无（未修改任何代码）