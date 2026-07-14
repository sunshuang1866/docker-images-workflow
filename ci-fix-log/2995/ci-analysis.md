# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, /bin/sh^M

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 框架内置测试脚本，非 PR 文件）
- 失败原因: 测试脚本 `bwa_test.sh` 使用 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh` 行尾携带 `\r`（日志中显示为 `^M`），内核将解释器误识别为不存在的 `/bin/sh\r`，脚本执行失败

### 与 PR 变更的关联
- PR 变更仅涉及 4 个文件（`Dockerfile`、`README.md`、`image-info.yml`、`meta.yml`），均不包含任何测试脚本
- Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均成功完成：日志中 `#7 DONE` 确认编译成功、`#8 pushing manifest` 确认镜像已推送到 registry，说明 PR 中的 Dockerfile 本身没有问题
- 失败发生在 `[Check]` 阶段，该阶段执行 CI 框架（`eulerpublisher`）预置的测试脚本 `bwa_test.sh` 对已构建镜像进行上架前校验，该脚本的换行符格式错误与本次 PR 的代码变更无关
- **结论**: 失败为 CI 测试基础设施的预置问题，非 PR 变更引起

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需将 `eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh` 文件的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新提交到 `eulerpublisher` 仓库，CI 下次克隆时将自动生效。本次 PR 本身无需任何代码修改即可重新触发构建。

## 需要进一步确认的点
- 确认 `eulerpublisher` git 仓库中 `tests/container/app/bwa_test.sh` 的原始换行符状态，以及是否仅该脚本存在此问题还是其他测试脚本同样受影响
- 确认 CI 构建节点上 git 的 `core.autocrlf` 配置是否导致 checkout 时 CRLF 未被自动转换为 LF

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本次失败为 CI 基础设施中测试脚本的换行符格式问题，修复不涉及对第三方/上游源文件的正则匹配变更。
