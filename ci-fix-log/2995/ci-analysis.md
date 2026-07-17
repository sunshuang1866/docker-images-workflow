# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 环境中 eulerpublisher 包的测试脚本 `bwa_test.sh`（shebang 行）
- 失败原因: eulerpublisher 包中内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（即 `^M`）被当作解释器名称的一部分，系统尝试查找名为 `/bin/sh\r` 的可执行文件，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
与 PR 无关。此次 PR 仅新增了 bwa 0.7.18 的 Dockerfile（Docker 构建、打包、推送均成功完成，日志中 `[Build] finished` 和 `[Push] finished` 均正常输出），失败发生在 CI 基础设施的 eulerpublisher 工具内置测试脚本上，该脚本自身存在 CRLF 换行符问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 文件的换行符从 CRLF（`\r\n`）转换为 LF（`\n`），或通过 `sed -i 's/\r$//'` 在 CI 运行环境中去除回车符后再执行。

## 需要进一步确认的点
- 确认 eulerpublisher 包的发布版本中 `bwa_test.sh` 是否确实使用了 CRLF 换行符，以及是否有其他类似测试脚本存在同样问题。
- 若 eulerpublisher 包由 CI 流水线动态克隆，需确认克隆环节中是否有文件被意外转换换行符（如 git 的 `core.autocrlf` 配置问题）。

## 修复验证要求
无需验证（infra-error，非 PR 代码问题，需 CI 运维侧修复 eulerpublisher 包中的测试脚本）。若尝试在 PR 侧绕过，可在此 Dockerfile 的 CI 触发配置中跳过 bwa_test.sh 检查，但这属于临时方案。
