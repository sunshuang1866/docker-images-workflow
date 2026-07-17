# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含CRLF换行符
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `CRLF`, `carriage return`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking .../bwa:0.7.18-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: CI 工具链 `eulerpublisher` 包中内置的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 Linux 内核将 shebang 行 `#!/bin/sh\r` 解释为寻找名为 `/bin/sh\r` 的解释器，该文件不存在因而脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile 构建完全成功——日志中可见 Docker build 阶段 `#7 DONE 199.0s`（编译安装 bwa 完成）、`#8 exporting to image`（镜像导出成功）、`[Build] finished` 和 `[Push] finished` 均正常完成。失败发生在后续的 `[Check]` 阶段，由 CI 基础设施中预先安装的 `eulerpublisher` 包所携带的测试脚本 `bwa_test.sh` 含有 CRLF 行尾所致，与本次 PR 的四项文件变更（Dockerfile、README.md、image-info.yml、meta.yml）均无任何关联。

## 修复方向

### 方向 1（置信度：高）
CI 基础设施维护者需要修复 `eulerpublisher` Python 包中分发的 `bwa_test.sh` 测试脚本，将其行尾从 CRLF 转换为 LF。可使用 `dos2unix` 或在 Git 仓库中设置 `.gitattributes` 强制该文件使用 LF 行尾。

### 方向 2（无需修复，仅说明）
本次 PR 本身的代码变更无需任何修改。Docker 镜像构建和推送均成功完成，待 CI 基础设施修复 `bwa_test.sh` 的行尾问题后，重新触发 CI 即可通过。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 的行尾格式，并排查是否还有其他测试脚本也存在同样问题。
2. 确认该脚本是否是在最近的 eulerpublisher 版本更新中引入了 CRLF（例如在 Windows 环境编辑后提交），以确保不会在未来版本中复现。
3. 确认 CI runner 上安装的 eulerpublisher 版本是否已包含对该问题的修复。

## 修复验证要求
（无——此问题为 infra-error，与 PR 代码变更无关，无需 code-fixer 修改任何项目文件。）
