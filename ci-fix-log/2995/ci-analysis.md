# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, bwa_test.sh, eulerpublisher, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 变更内容）
- 失败原因: CI 编排工具 `eulerpublisher` 中内置的 `bwa_test.sh` 测试脚本文件包含 Windows 风格换行符（CRLF，即 `\r\n`），其 shebang 行 `#!/bin/sh\r` 被 Linux 内核解析为解释器路径 `/bin/sh^M`，该路径不存在，导致脚本无法执行，[Check] 阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）构建和推送均成功完成：
- `[Build] finished`（日志 `#7 DONE 199.0s`，构建 2/2 步骤全部成功）
- `[Push] finished`（日志 `#8 DONE 8.4s`，镜像推送成功）

失败仅发生在 CI 框架的 [Check] 测试阶段，由 `eulerpublisher` Python 包自带的 `bwa_test.sh` 测试脚本的 CRLF 行尾问题引起。Docker 镜像本身构建正确，PR 代码无任何问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要对 `eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh` 文件进行换行符修复：将 CRLF（`\r\n`）转换为 LF（`\n`）。可通过 `dos2unix` 命令或在 Git 仓库中配置 `.gitattributes` 的 `text=auto` 来确保文件以 Unix 行尾检出。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `bwa_test.sh` 的当前行尾格式（CRLF vs LF）
- 确认该问题是否同样影响其他应用镜像（如已有其他镜像的 test 脚本也存在 CRLF 问题）
- 若 `eulerpublisher` 仓库本身行尾正确，则需排查 CI 环境中 `git clone` 时 `core.autocrlf` 配置是否导致行尾转换异常
