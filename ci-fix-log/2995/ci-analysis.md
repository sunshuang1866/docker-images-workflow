# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, /bin/sh, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: `bwa_test.sh` 文件包含 Windows 风格行尾（CRLF，即 `\r\n`），shebang 行 `#!/bin/sh` 实际被解析为 `#!/bin/sh\r`，导致 Shell 找不到名为 `/bin/sh\r` 的解释器，报 "bad interpreter" 错误。

### 与 PR 变更的关联
PR 变更（新增 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件）本身**没有问题**。Docker 构建阶段（`#7 [2/2] RUN ...`）完整通过，bwa 编译成功，镜像构建和推送均已完成（`[Build] finished`、`[Push] finished`）。失败发生在构建后的 CI [Check] 测试阶段，根因是 eulerpublisher CI 基础设施中的 `bwa_test.sh` 测试脚本文件包含了 Windows 换行符（CRLF），导致该脚本无法被 `/bin/sh` 执行。PR 代码无需修改。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 文件的行尾从 CRLF 转换为 LF（Unix 格式）。可以使用 `dos2unix` 或 `sed -i 's/\r$//'` 将文件中的 `\r` 字符移除，然后重新提交到 eulerpublisher 仓库。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 eulerpublisher 仓库中是否由本次 PR 的作者新增，还是之前就存在但未触发过 Check（因为此前无 24.03-lts-sp4 的 bwa 镜像触发该测试路径）。如果是新文件，需确认该文件在上传到 eulerpublisher 时是否经过 Windows 环境编辑。
- 检查 eulerpublisher 仓库中其他测试脚本（如同目录下其他 `*_test.sh` 文件）是否也存在类似的 CRLF 问题。

## 修复验证要求
修复 eulerpublisher 中 `bwa_test.sh` 的 CRLF 问题后，重新触发 CI：CI 应在 [Build] 和 [Push] 阶段继续通过，且 [Check] 阶段中 `bwa_test.sh` 应能正常启动执行。若 `bwa_test.sh` 执行后还有其他测试用例失败（非脚本解释器层面），则需要进一步排查测试逻辑本身的问题。
