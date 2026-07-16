# 修复摘要

## 修复的问题
CI 失败为 infra-error，根因是 eulerpublisher CI 工具包自带的测试脚本 `bwa_test.sh` 使用了 Windows 风格换行符（CRLF），与 PR 代码变更无关，无需修改任何源代码文件。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：
- Docker 镜像构建和推送均已成功完成（`[Build] finished`、`[Push] finished`）
- 失败仅发生在 `[Check]` 阶段，错误信息为 `bad interpreter: /bin/sh^M`，表明 `bwa_test.sh` 文件使用了 CRLF 换行，导致 shebang 行被错误解析
- 该文件属于 eulerpublisher CI 工具包（`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`），不在本仓库内，**与 PR 的 4 个变更文件完全无关**

此问题需要由 eulerpublisher 包的维护者修复，即将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF。修复后重新触发 CI 即可通过 Check 阶段。

## 潜在风险
无