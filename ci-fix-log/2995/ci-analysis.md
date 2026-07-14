# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 `eulerpublisher` 内 BWA 镜像的后置测试脚本）
- 失败原因: `bwa_test.sh` 文件含有 Windows 风格的 CRLF 换行符，shebang 行 `#!/bin/sh` 尾部多出回车符 `\r`，变为 `#!/bin/sh\r`，系统无法找到名为 `/bin/sh\r` 的解释器。

### 与 PR 变更的关联
该失败与 PR 的代码变更**无关**。日志显示 Docker 镜像构建和推送均已完成且成功：
- `[Build] finished`、`[Push] finished`
- 镜像 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64` 已成功推送到 registry

失败仅发生在 CI 基础设施的 `[Check]` 后置测试步骤，属于 `eulerpublisher` 工具自带测试脚本的换行符格式问题。PR 新增/修改的文件（Dockerfile、README.md、meta.yml、image-info.yml）均正确无误。

## 修复方向

### 方向 1（置信度: 高）
该问题不属于 PR 作者需要修复的范围。CI 基础设施维护者需将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`），并在 `eulerpublisher` 上游仓库中确保以 Unix 换行符保存。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 `eulerpublisher` 上游仓库中是否确实存在 CRLF 换行符（可能是最近新增的文件且在 Windows 环境下编辑提交）。
- 排查 `eulerpublisher` 仓库中其他应用的测试脚本是否也存在同样的 CRLF 问题，避免批量影响。
- 若该 PR 同时触发 aarch64 架构构建，需确认 aarch64 job 的 [Check] 步骤是否也命中同一问题。
