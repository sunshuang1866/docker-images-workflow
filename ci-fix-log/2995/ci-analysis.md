# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454-INFO: [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 包中的测试脚本，shebang 行）
- 失败原因: eulerpublisher 包中分发的 `bwa_test.sh` 测试脚本行尾为 CRLF（Windows 格式），Linux shell 将 shebang 中的 `\r` 视为解释器路径的一部分，尝试执行 `/bin/sh\r` 导致 `bad interpreter: No such file or directory`

### 与 PR 变更的关联

**与 PR 变更无关**。日志显示 Docker 镜像的构建（`[Build] finished`）和推送（`[Push] finished`）均成功完成，BWA 0.7.18 源码在 openEuler 24.03-LTS-SP4 基础镜像上编译通过（#7 DONE 199.0s）。失败仅发生在 eulerpublisher CI 工具的 `[Check]` 阶段，因该工具分发的 `bwa_test.sh` 文件包含 CRLF 行尾，属于 CI 基础设施问题，与本次 PR 新增的 Dockerfile 及元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
CI 维护方需修复 eulerpublisher 包中的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 文件，将其行尾从 CRLF 转换为 LF。修复后重新安装/重新部署 eulerpublisher 包即可。PR 提交者无需对本次 PR 做任何修改。

## 需要进一步确认的点

- 确认 eulerpublisher 包中 `bwa_test.sh` 的行尾问题是否为包构建/分发流程引入（如 Git 在 Windows 上 checkout 时 `core.autocrlf` 导致），以防止其他应用的测试脚本也存在同类问题
- 确认该 `bwa_test.sh` 的来源仓库和版本，以便从源头上修复 CRLF 问题

## 修复验证要求

无。本次失败为 `infra-error`，与 PR 代码变更无关，Code Fixer 无需处理 PR 代码。
