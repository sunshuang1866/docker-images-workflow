# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含CRLF换行
- 新模式症状关键词: `bad interpreter, /bin/sh^M, No such file or directory, ^M`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ... bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: CI 测试基础设施中的 `bwa_test.sh` 脚本包含 DOS/Windows 换行符（CRLF，即 `\r\n`），导致 shebang 行被解析为 `/bin/sh\r`，内核无法找到该解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

**与 PR 变更无关。** 证据如下：

1. Docker 镜像构建完全成功 —— 日志显示 Docker build 所有步骤（yum 安装、bwa 源码编译、镜像导出与推送）均正常完成（`#7 DONE 199.0s`，`#8 DONE 8.4s`），PR 新增的 Dockerfile 语法和编译流程均正确无误。
2. 失败发生在构建之后的 `[Check]` 阶段，调用的是 CI 系统 eulerpublisher 包内置的测试脚本 `bwa_test.sh`，该脚本**不在 PR 的文件变更范围内**（PR 仅变更了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`）。
3. 错误信息中的 `^M` 字符（回车符 `\r`）是 Windows 换行格式的标志，属于 CI 基础设施侧的文件格式问题，与 PR 提交的代码无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 eulerpublisher 包中的 `bwa_test.sh` 文件的换行格式：将其从 CRLF (`\r\n`) 转换为 LF (`\n`)。在 CI runner 上执行 `dos2unix` 或 `sed -i 's/\r$//'` 对 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 进行转换即可。此修复必须由有 CI 基础设施写权限的运维人员执行，Code Fixer 无法处理。

## 需要进一步确认的点
- 确认其他应用镜像的 `*_test.sh` 脚本是否也存在同样的 CRLF 换行问题（属于 CI 基础设施的批量文件格式问题，可能与 eulerpublisher 包的打包/部署流程有关）。
- 确认在修复后重新触发 PR #2995 的 CI 流程，验证 Check 阶段能通过（因为 Docker 构建本身是正常的）。

## 修复验证要求
无。此失败为 infra-error，Code Fixer 不需要也不应提交任何代码修改。
