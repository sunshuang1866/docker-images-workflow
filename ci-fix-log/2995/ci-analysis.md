# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, /bin/sh^M, CRLF, line endings

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本，非 PR 变更文件）
- 失败原因: 测试脚本 `bwa_test.sh` 的文件行尾为 Windows 风格的 CRLF（`\r\n`）而非 Unix 风格的 LF（`\n`）。Shebang 行 `#!/bin/sh` 因末尾的 `\r` 被解析为 `#!/bin/sh^M`，操作系统找不到名为 `/bin/sh\r` 的解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**无直接关联**。PR 仅新增了一个 Dockerfile 及关联的元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像构建和推送均已成功完成：

```
#7 DONE 199.0s  (镜像构建成功)
#8 DONE 8.4s   (镜像导出和推送成功)
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
```

失败仅发生在 CI 管线的 [Check] 阶段，因 eulerpublisher 系统包中预置的 `bwa_test.sh` 测试脚本自身的文件格式问题（CRLF 行尾）导致无法执行，与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
将 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（或其他对应路径的 bwa 测试脚本源文件）的行尾从 CRLF 转换为 LF。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理。该修复应在 CI 基础设施侧（eulerpublisher 包或 CI 测试脚本仓库）进行，无需修改 PR 中的任何文件。

## 需要进一步确认的点
1. `bwa_test.sh` 的源文件托管位置（是 eulerpublisher 源码仓库还是 CI 配置仓库），以便定位并修复 CRLF 问题。
2. 该测试脚本是否仅为本次 x86-64 构建使用，还是也用于 aarch64 架构的 Check 阶段——若 aarch64 也有相同的测试步骤，该架构也会因同一问题失败。
3. 是否存在 `bwa_test.sh` 的 Git 仓库，确认其 `.gitattributes` 配置是否遗漏了 `*.sh text eol=lf` 导致该文件被错误地以 CRLF 提交。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——该失败为 infra-error，修复涉及 CI 基础设施侧的纯文本格式转换，不涉及正则 patch 上游源文件。
