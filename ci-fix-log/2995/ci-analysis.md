# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `bwa_test.sh`, `CRLF`, Windows line endings

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`eulerpublisher` 包中的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: 测试脚本 `bwa_test.sh` 使用 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，导致系统尝试查找解释器 `/bin/sh\r`（实际不存在），报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 构建完全成功：日志中 Docker build 10 步全部通过（`#7 DONE 199.0s`），镜像构建和推送完成（`[Build] finished`、`[Push] finished`）。失败发生在 CI 基础设施的 [Check] 阶段，由 `eulerpublisher` 工具包自带的 `bwa_test.sh` 测试脚本因 CRLF 行尾问题无法执行导致。该脚本位于系统路径 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`，不属于 PR 仓库中的任何文件。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施的 `bwa_test.sh` 测试脚本文件包含 Windows 换行符（CRLF），需要由 CI 维护者将脚本的行尾转换为 Unix 格式（LF）。可通过 `dos2unix` 命令或在 CI 环境中自动化处理：
- 修复 `eulerpublisher` 包中的测试脚本源文件，确保所有 `.sh` 文件使用 LF 行尾
- 在 CI 运行 [Check] 阶段前自动执行 `dos2unix` 或 `sed -i 's/\r$//'` 清理脚本

## 需要进一步确认的点
- 无。日志证据充分，Docker 构建成功、测试脚本 CRLF 行尾是明确根因，无需进一步排查。

## 修复验证要求
此失败为 infra-error，修复不在本 PR 范围内。若需本 PR 配合验证：
- 在 CI 环境中确认 `dos2unix /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或等效命令执行后，重新触发 PR 的 CI 流水线，[Check] 阶段应能正常通过。
