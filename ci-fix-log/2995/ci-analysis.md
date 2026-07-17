# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本行尾格式错误
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`, `CRLF`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 变更内容）
- 失败原因: eulerpublisher 包中自带的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，即 `\r\n`）。脚本 shebang 行 `#!/bin/sh` 末尾的 `\r` 被内核当作解释器路径的一部分，导致系统尝试执行 `/bin/sh\r`（不存在的可执行文件），报 `bad interpreter`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像**构建和推送均已成功完成**（日志中可见 `[Build] finished`、`[Push] finished`，buildkit 所有步骤均返回 `DONE`）。失败发生在 CI 流水线后续的镜像验证（Check）阶段，由 eulerpublisher CI 工具包自带的测试脚本行尾格式错误导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，Code Fixer **无需处理此 PR**。应通知 CI 维护者修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件的换行符格式——将该文件的行尾从 CRLF（`\r\n`）转换为 LF（`\n`）。可以使用 `dos2unix` 或在 eulerpublisher 源码仓库中配置 `.gitattributes` 强制该文件以 LF 检出。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 eulerpublisher 源码仓库中是否为 CRLF 格式（可能是在 Windows 环境编辑后提交的）。
- 确认 eulerpublisher 包安装过程是否保留了原始文件的行尾格式（pip install 通常不会转换行尾）。

## 修复验证要求
无需验证（infra-error，不在 PR 修改范围内）。
