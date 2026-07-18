# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```
- Docker 构建成功（bwa 编译通过，镜像构建并推送成功）
- 失败发生在 CI [Check] 阶段的测试脚本执行环节

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 新增文件）
- 失败原因: CI 系统中的 `bwa_test.sh` 测试脚本包含 Windows 行尾格式（CRLF，即 `\r\n`），导致 shebang 行被解析为 `#!/bin/sh\r`（即 `#!/bin/sh^M`），`/bin/sh` 无法识别该解释器路径，脚本执行失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 的改动仅限于：
- 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`
- 更新 `HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`

Docker 镜像构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`），仅在 CI 后置 `[Check]` 阶段因基础设施脚本的 CRLF 行尾问题报错。PR 代码本身无任何问题。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 基础设施中 `eulerpublisher` 包的 `bwa_test.sh` 测试脚本，将其行尾格式从 CRLF（`\r\n`）转换为 LF（`\n`）。可在 CI 流水线中执行 `sed -i 's/\r$//' /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或从上游 `eulerpublisher` 仓库修复该脚本的行尾格式。

## 需要进一步确认的点
- 确认 `eulerpublisher` 上游仓库中 `bwa_test.sh` 的行尾格式是否为 LF（若为 CRLF，需在上游修复）
- 确认该 CI runner 是否为新建环境（若同为 SP4 的新增 runner，其他使用 `eulerpublisher` 测试脚本的镜像构建也可能遭遇同类问题）
- 确认 `bwa_test.sh` 是否仅影响 bwa 镜像，还是 `eulerpublisher/tests/container/app/` 目录下其他测试脚本也有 CRLF 问题
