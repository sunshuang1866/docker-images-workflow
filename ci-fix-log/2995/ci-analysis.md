# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本 CRLF 换行
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, test failed

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 工具链测试脚本 `eulerpublisher/tests/container/app/bwa_test.sh`（shebang 行）
- 失败原因: 该测试脚本的 shebang 行结尾包含 Windows 风格的 CRLF 换行符（`\r\n`），导致系统将解释器路径解析为 `/bin/sh^M`（而非 `/bin/sh`），内核报 "bad interpreter: No such file or directory"，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、image-info.yml、meta.yml），未修改任何 CI 测试脚本。Docker 镜像的构建和推送阶段均成功完成（日志中可见 `[Build] finished` 和 `[Push] finished`），失败仅发生在 CI 基础设施的 `[Check]` 阶段——执行 `bwa_test.sh` 测试脚本时因 Windows 换行符问题崩溃。这是 CI 基础设施的问题，不影响 PR 提交的 Dockerfile 正确性。

## 修复方向

### 方向 1（置信度: 高）
CI 维护者将 `eulerpublisher` 仓库中的测试脚本 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'` 命令），确保所有 CI 测试脚本以 Unix 换行符格式存储。

## 需要进一步确认的点
无。错误信息明确，根因清晰：CI 测试脚本带有 Windows 行尾符导致 shebang 解析失败。

## 修复验证要求
无。此为 CI 基础设施问题，与 PR 代码无关，无需 code-fixer 处理 Dockerfile 或相关文件。
