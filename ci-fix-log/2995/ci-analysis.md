# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, CRLF, shebang

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段的 `bwa_test.sh` 测试脚本（路径：`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 工具链 eulerpublisher 中的 bwa 测试脚本 `bwa_test.sh` 使用了 Windows 换行符（CRLF `\r\n`）。操作系统在解析 shebang 行 `#!/bin/sh` 时，因为末尾携带回车符 `\r`（日志中显示为 `^M`），将解释器路径识别为 `/bin/sh\r`，而该路径不存在，导致 `bad interpreter: No such file or directory` 错误。

### 与 PR 变更的关联
PR #2995 的变更（新增 bwa 0.7.18 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及元数据文件）与本次失败**无关**。Docker 镜像构建完全成功：
- 依赖安装（make, gcc, zlib-devel）成功
- bwa 源码下载和解压成功
- `make clean && make -j "$(nproc)"` 编译成功（仅有两个无害的 `-Wunused-but-set-variable` 编译警告）
- 镜像构建、导出、推送到 Docker Registry 均成功（`[Build] finished`, `[Push] finished`）

失败仅发生在 CI 基础设施的 [Check] 测试阶段，`bwa_test.sh` 测试脚本本身的换行符问题导致脚本无法执行，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 工具链 `eulerpublisher` 仓库中的 `bwa_test.sh` 测试脚本，将其换行符从 CRLF 转换为 LF。

修复步骤（需在 eulerpublisher 仓库中操作，不在当前 PR 范围内）：
1. 在 `eulerpublisher` git 仓库中定位 `tests/container/app/bwa_test.sh`
2. 将文件换行符转换为 Unix 格式（使用 `dos2unix` 或 `sed -i 's/\r$//'` 命令）
3. 提交修复至 eulerpublisher 仓库

此项修复需由 CI 基础设施维护者处理，Code Fixer 无需修改 PR 中的任何文件。

### 方向 2（置信度: 低）
如果 `bwa_test.sh` 不存在于 eulerpublisher 仓库中（即是在 CI 运行时从其他来源动态生成或复制的），则需要排查该脚本的来源和生成逻辑，确保生成过程不引入 Windows 换行符。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 是否确实存在，其内容是否使用 CRLF 换行符（可执行 `file` 命令检查或 `od -c` 查看 `\r` 字符）
2. 确认该换行符问题是仅 bwa 的测试脚本受影响，还是所有应用的测试脚本都有相同问题（可抽查其他已存在的测试脚本）
3. 确认现有 bwa 版本（如 `0.7.18-oe2203sp3`）的 CI [Check] 是否也存在相同失败——若存在，则进一步确认为积压的 infra 问题，与该 PR 的关联度为零

## 修复验证要求
N/A — 此为 infra-error，修复操作不在当前 PR 的代码范围内，无需 Code Fixer 提交任何代码变更。CI 工具的修复需在 eulerpublisher 仓库中完成，验证方式为：转换后的 `bwa_test.sh` 脚本能够正常执行，[Check] 阶段通过。
