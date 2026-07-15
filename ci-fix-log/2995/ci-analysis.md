# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh, /bin/sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: `eulerpublisher` 测试框架中的 `bwa_test.sh` 脚本文件使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 内核找不到名为 `/bin/sh\r` 的解释器，测试脚本无法执行，[Check] 阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 构建和镜像推送均已成功完成（日志中可见 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`、manifest 推送成功）。失败发生在 CI 的 [Check] 后处理阶段，根因是 CI 基础设施中 `eulerpublisher` 测试套件的 `bwa_test.sh` 文件携带了 CRLF 换行符。PR 中不包含任何测试脚本变更。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 的换行符问题：将该文件从 CRLF（`\r\n`）转换为 LF（`\n`），可用 `dos2unix` 或 `sed -i 's/\r$//'` 处理，确保 shebang 行 `#!/bin/sh` 不含末尾 `\r`。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 是否为新添加的测试文件（与 bwa 镜像支持同步引入）。若是，文件在提交时未正确处理换行符；若不是新文件，则可能是最近的 eulerpublisher 版本更新引入了损坏的脚本文件。
- 日志仅包含 x86-64 架构的构建和检查过程，如果 CI 还在其他架构（aarch64）上运行并失败，需获取对应日志进行验证。
