# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, CRLF, line endings

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh:1`（shebang 行）
- 失败原因: eulerpublisher CI 工具的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF）。shebang 行 `#!/bin/sh` 末尾附带了 `\r` 字符，导致内核尝试查找 `/bin/sh\r` 这一不存在的解释器，报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送均成功完成（日志中 `[Build] finished`、`[Push] finished` 均无异常）。失败发生在 CI 框架自身的 [Check] 测试阶段，测试脚本 `bwa_test.sh` 属于 eulerpublisher 包的内置文件，其 CRLF 行尾问题与 PR 提交的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
eulerpublisher CI 工具包中的 `bwa_test.sh` 文件使用了 Windows 风格换行符（CRLF），需将其转换为 Unix 风格换行符（LF）。修复应在上游 eulerpublisher 仓库中进行：对 `tests/container/app/bwa_test.sh`（以及可能存在的其他测试脚本）执行 `dos2unix` 或用 `sed -i 's/\r$//'` 去除行尾 `\r` 字符。此修复不涉及本 PR 的任何文件变更。

## 需要进一步确认的点
- 确认 eulerpublisher 包中 `bwa_test.sh` 的换行符格式是否确实为 CRLF（通过 `od -c` 或 `file` 命令检查）
- 确认 eulerpublisher 包的其他测试脚本（如 `tests/container/app/` 目录下其他 `*_test.sh`）是否也存在同样的 CRLF 污染问题
