# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本DOS换行符
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 `eulerpublisher` 包内测试脚本）
- 失败原因: CI 测试脚本 `bwa_test.sh` 使用 DOS/Windows 换行格式（CRLF，`\r\n`），其中 shebang 行 `#!/bin/sh\r` 被内核解析为试图查找名为 `/bin/sh\r`（含回车符）的解释器，该文件不存在，导致 `bad interpreter` 错误。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 只新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
- `HPC/bwa/README.md`（新增一行标签文档）
- `HPC/bwa/doc/image-info.yml`（新增一个标签条目）
- `HPC/bwa/meta.yml`（新增一个版本条目）

Docker 镜像构建和推送均**成功完成**（`[Build] finished`、`[Push] finished`，Docker 构建日志显示所有步骤均正常）。失败发生在 CI 的 `[Check]` 后置阶段，由 `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本的换行符问题导致。PR 本身无错误，仅因新增 bwa 的 24.03-lts-sp4 变体而首次触发了该测试脚本的执行，暴露了 CI 工具中已有的缺陷。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包中的 `bwa_test.sh` 测试脚本需要将文件格式从 DOS 换行（CRLF）转换为 Unix 换行（LF）。使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该脚本文件即可解决。**此修复需在 eulerpublisher 包的源代码仓库中进行，不在 PR #2995 的修改范围内。**

### 方向 2（置信度: 低）
无法排除 `eulerpublisher` 包中其他测试脚本也存在同样换行符问题的可能性，建议对 `tests/container/app/` 目录下所有 `.sh` 文件进行批量换行符检查。

## 需要进一步确认的点
- `bwa_test.sh` 是在 eulerpublisher 包发布时引入的 DOS 换行符，还是由 CI 环境在某个文件传输环节（如 Git 的 `core.autocrlf` 设置）引入的。
- eulerpublisher 包中是否还有其他测试脚本（如 `HPC/` 目录下其他应用的 `_test.sh`）存在同样的换行符问题。

## 修复验证要求
不适用。此失败为 infra-error，修复需在 eulerpublisher 包中进行，与 PR #2995 的代码变更无关。PR #2995 的 Dockerfile 构建已通过，无需验证。
