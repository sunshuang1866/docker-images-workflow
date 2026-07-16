# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher CI 工具包中的 `bwa_test.sh`（`/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: 该测试脚本的 shebang 行末尾包含 Windows 风格回车符（`\r`/`^M`），导致系统尝试将 `#!/bin/sh\r` 作为解释器路径查找，因路径无效而报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 代码变更无关**。所有构建步骤（`make` 编译、Docker 镜像构建、Registry 推送）均成功完成——日志中可见 `#8 DONE`、`[Build] finished`、`[Push] finished`。失败仅发生在 CI 框架层 `eulerpublisher` 的 [Check] 阶段，原因是被调用的 `bwa_test.sh` 自身包含 CRLF 行尾。该文件属于 eulerpublisher 安装包（路径 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`），不在本 PR 的仓库范围内，PR 作者无法修复。

## 修复方向

### 方向 1（置信度: 高）
**由 eulerpublisher CI 工具链维护者处理**：将 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF（Unix 换行符）。PR 作者对本仓库无需做任何修改，可等待 CI 基础设施修复后重跑流水线。

## 需要进一步确认的点
1. 确认 eulerpublisher 仓库中 `bwa_test.sh` 是否为近期新增文件（若为存量文件，需排查是否有其他镜像的 CI 也已受此影响但未被发现）
2. 修复后需验证 `bwa_test.sh` 在 openEuler 24.03-LTS-SP4 环境下对 bwa 镜像的功能性测试是否正常通过
