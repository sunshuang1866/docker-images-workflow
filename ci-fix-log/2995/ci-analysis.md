# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本换行符错误
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 系统 `eulerpublisher` 包内置测试脚本 `eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: 该测试脚本使用了 Windows 换行格式（CRLF），文件头部的 shebang 行 `#!/bin/sh` 末尾带有回车符 `\r`，内核将其解释为解释器路径 `/bin/sh\r`，该路径不存在，导致脚本无法执行。Docker 镜像的构建和推送本身均已成功完成（`[Build] finished`、`[Push] finished`、`#8 DONE`）。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 的 Dockerfile 构建完全成功——yum 安装依赖、源码下载编译、产物提取、依赖清理均正常完成，镜像成功导出并推送到 registry。失败发生在构建后的 CI 校验阶段（`[Check]`），由 `eulerpublisher` 工具的测试脚本自身 CRLF 换行符问题导致，属于 CI 基础设施 bug。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 工具源码仓库（CI 中通过 `git clone` 获取）中的 `tests/container/app/bwa_test.sh` 文件使用了 Windows 换行符（CRLF），需要用 `dos2unix` 或在提交时确保该文件以 Unix 换行符（LF）存储。修复不在本 PR 仓库范围内，需在 `eulerpublisher` 的上游仓库中修正 `bwa_test.sh` 文件换行格式，或 CI 流水线在安装 `eulerpublisher` 后对测试脚本执行 `sed -i 's/\r$//'` 操作。

## 需要进一步确认的点
- 该测试脚本 `bwa_test.sh` 的具体内容（其测试逻辑是否合理），当前日志中仅能看到脚本本身无法执行
- `eulerpublisher` 仓库中是否还有其他测试脚本存在同样的 CRLF 问题
- 该 CI 节点的 `eulerpublisher` 版本是否为最新，上游是否已修复此问题
