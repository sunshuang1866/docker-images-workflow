# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本DOS换行符
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 基础设施中的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: CI 测试脚本 `bwa_test.sh` 的 shebang 行包含 Windows 风格换行符（CRLF），`#!/bin/sh` 末尾的 `\r`（日志中显示为 `^M`）导致内核尝试以 `/bin/sh\r` 作为解释器执行脚本，而该文件路径不存在，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（`[Build] finished`）和推送（`[Push] finished`）均已成功完成。该 Dockerfile 在 openEuler 24.03-LTS-SP4 基础镜像上正确安装了依赖、编译了 bwa 0.7.18 并输出了二进制文件。失败完全发生在 CI 基础设施的 `[Check]` 阶段——`eulerpublisher` 工具试图运行预先部署在 CI runner 上的测试脚本 `bwa_test.sh`，但该脚本文件本身因 DOS 换行符而无法被内核解释执行。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施团队需修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件的换行符问题：将 CRLF（`\r\n`）转换为 LF（`\n`）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 操作该文件后重新部署 eulerpublisher 包到 CI runner。此问题与本次 PR 的代码变更无关，PR 本身无需修改。

## 需要进一步确认的点
- 确认 CI runner 上 `bwa_test.sh` 文件是否确实存在 CRLF 换行符（通过 `file` 命令或 `cat -A` 检查）
- 确认是否有其他测试脚本同样受到影响（该问题可能是 eulerpublisher 包部署流程的系统性问题）
- 确认 `ARG TARGETARCH` 在 Dockerfile 中声明但未使用是否为预期行为（当前仅构建了 x86_64，若后续需支持 arm64 可能需要使用此变量）
