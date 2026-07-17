# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CRLF换行符污染
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 代码）
- 失败原因: CI 基础设施 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang `#!/bin/sh\r` 被解释为查找名为 `/bin/sh\r` 的解释器，该路径不存在，测试脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新了 README.md、image-info.yml、meta.yml 四个文件，不涉及 CI 基础设施中的 `bwa_test.sh` 脚本。Docker 镜像构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`），失败发生在 CI 后处理阶段的容器检查（Check）环节，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 运维团队需将 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh`（以及可能受影响的同批次其他 `*_test.sh` 文件）的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可通过 `dos2unix` 或在 CI 镜像构建流程中增加换行符规范化步骤来解决。PR 代码本身无需任何修改。

## 需要进一步确认的点
1. `bwa_test.sh` 是在何时被引入 `eulerpublisher` 包的（是否为该包最近一次更新引入的新文件，其行尾问题来自上游 Git 仓库的提交）
2. 是否还有其他 `eulerpublisher/tests/container/app/` 下的 `*_test.sh` 脚本存在同样的 CRLF 问题（可批量检查）
3. aarch64 架构的下游构建 job 日志未提供，无法确认 aarch64 构建是否也因同一 Check 阶段失败而受阻
