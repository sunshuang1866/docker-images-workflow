# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454-INFO: [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施 eulerpublisher 工具内的测试脚本）
- 失败原因: eulerpublisher CI 工具提供的 `bwa_test.sh` 测试脚本文件使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 末尾多出一个不可见的回车符 `\r`（日志中显示为 `^M`）。系统尝试将 `/bin/sh\r` 作为解释器执行，但该路径不存在，报 `bad interpreter`。Docker 镜像本身的构建和推送均已完成且成功。

### 与 PR 变更的关联
**与 PR 无关。** PR #2995 新增的 Dockerfile 构建完全成功：
- `yum install` 依赖安装成功（17 个包全部安装并验证）
- BWA 0.7.18 源码下载、解压、编译成功（仅有编译器 warning，无 error）
- 镜像导出并推送成功（`[Build] finished`、`[Push] finished`）

失败发生在 CI 流水线的 `[Check]` 阶段，由 eulerpublisher 基础设施中的 `bwa_test.sh` 脚本自身携带 CRLF 换行符导致，不涉及 PR 的任何代码变更。

## 修复方向

### 方向 1（置信度: 高）
修复 eulerpublisher CI 工具仓库中 `tests/container/app/bwa_test.sh` 文件的换行符，将 CRLF（`\r\n`）转换为 LF（`\n`）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后提交到 eulerpublisher 仓库。

## 需要进一步确认的点
- 确认 eulerpublisher 仓库中 `bwa_test.sh` 是否确实使用了 CRLF 换行符（大概率是 git 在不同平台间传输时或编辑器设置了错误的换行模式导致）
- 检查 eulerpublisher 仓库中是否还有其他测试脚本存在同样的 CRLF 问题（如 `*.sh` 文件批量检查）

## 修复验证要求
此问题为 CI 基础设施（eulerpublisher 工具）的文件格式问题，不涉及 PR #2995 的 Dockerfile 或应用镜像构建逻辑。修复需在 eulerpublisher 仓库中进行，而非本仓库。验证方式：修复后触发 CI 重跑，确认 `[Check]` 阶段通过。
