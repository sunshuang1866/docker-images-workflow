# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 环境的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包自带测试脚本）
- 失败原因: `bwa_test.sh` 文件的 shebang 行（`#!/bin/sh`）末尾带有 Windows CRLF 换行符（`\r\n`），导致系统尝试查找名为 `/bin/sh^M`（`^M` 即 `\r`）的解释器，该路径不存在，脚本无法执行。

### 与 PR 变更的关联
**无关**。PR 仅新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建和推送均已成功完成（日志中 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`）。失败发生在 CI [Check] 阶段执行 `bwa_test.sh` 时，该脚本属于 eulerpublisher CI 工具包，存在 Windows 换行符问题是 CI 基础设施的缺陷，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
`bwa_test.sh` 测试脚本的 shebang 行被写入了 Windows CRLF 换行符，需由 CI 基础设施维护者修复：将文件转换为 Unix LF 换行（`dos2unix` 或 `sed -i 's/\r$//'`），或重新生成该脚本。

### 方向 2（置信度: 中）
如果该脚本是由 CI 流水线的某个步骤动态生成或拷贝的，需要排查上游环节中引入 CRLF 的来源（如 Git 仓库未设置 `core.autocrlf` 导致 checkout 时转换了换行符）。

## 需要进一步确认的点
- `bwa_test.sh` 是 eulerpublisher 包自带的还是 CI 流程中从某个仓库克隆后动态生成的
- 该测试脚本是否在其他 `bwa` 镜像变体（如 22.03-lts-sp3）的 CI 构建中也存在同样的问题（若是，则说明近期 eulerpublisher 包的更新引入了 CRLF 缺陷）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本问题属于 CI 基础设施文件的换行符问题，与 PR 代码变更无关，无需 code-fixer 介入。
