# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, shebang, sh^M

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher` 包内测试文件 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 变更文件）
- 失败原因: CI 测试脚本 `bwa_test.sh` 的 shebang 行使用了 Windows 风格行尾（CRLF），内核将 `#!/bin/sh\r`（含回车符 `\r` 即 `^M`）误解释为解释器名称 `/bin/sh^M`，导致 "bad interpreter: No such file or directory" 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）构建成功——日志显示 `#7 DONE 199.0s`、`#8 DONE 8.4s`，镜像已成功构建并推送至 `docker.io/.../bwa:0.7.18-oe2403sp4-x86_64`。失败发生在 CI 流水线后续的 [Check] 阶段，是 eulerpublisher CI 框架内置的 `bwa_test.sh` 测试脚本自身存在 CRLF 行尾问题，该问题同样会影响其他 bwa 标签的测试。

## 修复方向

### 方向 1（置信度: 高）
`bwa_test.sh` 文件的 shebang 行末尾含回车符（`\r`），修复方向是将该文件的行尾从 CRLF 转换为 LF。这是 eulerpublisher 包内的文件，需要在 eulerpublisher 仓库中修复，而非在当前 PR 中修复。临时的 CI 侧 workaround 也可在测试执行前通过 `sed -i 's/\r$//'` 去除 `\r`。

## 需要进一步确认的点
- `bwa_test.sh` 的 CRLF 是其上游仓库（eulerpublisher）最近引入的，还是该文件一直存在此问题但此前该 runner 上未触发过 bwa 的 [Check] 阶段。
- 确认 eulerpublisher 包的版本及 `bwa_test.sh` 的内容，以确定需要上报给 eulerpublisher 维护者修复该文件的行尾格式。
