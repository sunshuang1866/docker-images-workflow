# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, test script, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包中的测试脚本）
- 失败原因: CI [Check] 阶段的测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF），导致 shebang 行被解析为 `#!/bin/sh\r`，内核查找名为 `/bin/sh\r` 的解释器失败，报 "bad interpreter: No such file or directory"

### 与 PR 变更的关联
此失败**与 PR 变更无关**。PR 新增的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）构建完全成功，日志清晰显示：

- 所有 7 个构建步骤均通过，BWA 0.7.18 编译成功
- 镜像导出并推送到 registry 成功（`#8 DONE 8.4s`）
- `[Build] finished` 和 `[Push] finished` 均正常

失败完全发生在 CI 基础设施的 [Check] 阶段，由 `eulerpublisher` 包中的测试脚本 `bwa_test.sh` 自身行尾格式问题导致。

## 修复方向

### 方向 1（置信度: 高）
将 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF。可以使用 `dos2unix` 或 `sed -i 's/\r$//'` 对该文件进行处理后重新提交到 eulerpublisher 仓库（非本 PR 仓库）。

### 方向 2（置信度: 低）
如果 eulerpublisher 包是从 Git 克隆后安装的，检查 eulerpublisher 仓库的 `.gitattributes` 配置，确保 `*.sh` 文件不会被自动转换为 CRLF。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 是否确实存在 CRLF 行尾问题
2. 确认其他镜像的测试脚本是否也存在同样的 CRLF 问题（如 `tests/container/app/` 目录下的其他 `*_test.sh` 文件）
3. 确认 eulerpublisher 仓库的 `.gitattributes` 中是否有针对 `*.sh` 的 `text=auto` 或 `eol=crlf` 等可能导致 Git 自动转换换行符的配置
