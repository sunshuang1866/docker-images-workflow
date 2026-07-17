# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因是 eulerpublisher CI 工具包中的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），导致 shebang 行被内核误读为 `/bin/sh\r`，属于 CI 基础设施问题，与 PR #2995 的代码变更无关。

## 修改的文件
无（infra-error，无需修改 PR 代码）

## 修复逻辑
- Docker 镜像构建和推送阶段均已成功完成（日志中 `[Build] finished`、`[Push] finished` 均正常）。
- 失败仅发生在 CI 的 [Check] 阶段，执行测试脚本 `bwa_test.sh` 时报错 `bad interpreter: /bin/sh^M`，原因是脚本文件使用 CRLF 换行格式。
- 该测试脚本位于 eulerpublisher CI 工具包内（`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`），不属于本仓库文件，也不在 PR 变更范围内。
- PR 新增的 Dockerfile、README.md、meta.yml、image-info.yml 均无语法或逻辑问题。
- 修复需要由 CI 基础设施维护者将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（如使用 `dos2unix` 或 `sed -i 's/\r$//'`）。

## 潜在风险
无。该修复属于 CI 基础设施层面，不影响本仓库任何代码。