# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含Windows换行符
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上已安装的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内测试脚本）
- 失败原因: `bwa_test.sh` 脚本的第一行 shebang（`#!/bin/sh`）末尾带有 Windows 风格的 CRLF 换行符（`\r\n`），导致内核将 `/bin/sh^M`（`^M` 即 `\r`）当作解释器路径，该路径不存在，脚本无法执行。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅涉及新增 Dockerfile、更新 README.md、image-info.yml 和 meta.yml。Docker 镜像构建完全成功（编译、构建、推送三个阶段均通过），失败仅发生在 CI 后处理阶段的 [Check] 步骤——该步骤执行的 `bwa_test.sh` 测试脚本是 eulerpublisher 工具包自带的 CI 基础设施文件，其 Windows 换行符问题与 PR 代码变更无任何因果关系。

具体证据：
- Dockerfile 中 `make` 编译成功，生成 bwa 二进制 (#7 197.9)
- 镜像导出和推送成功 (`#8 DONE 8.4s`，`[Build] finished`，`[Push] finished`)
- 唯一失败点：eulerpublisher 在 [Check] 阶段调用自带的 `bwa_test.sh` 时因 CRLF 换行符导致内核拒绝执行

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施问题，**Code Fixer 无需处理此 PR**。需要 CI 维护者修复 eulerpublisher 包中的 `bwa_test.sh` 文件：
- 将 `bwa_test.sh` 的换行符从 CRLF (`\r\n`) 转换为 LF (`\n`)，可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理。
- 确认 eulerpublisher 包的构建/发布流程中是否存在导致 Windows 换行符混入的环节（如 Windows 开发环境、Git 配置 `core.autocrlf=true` 等）。

## 需要进一步确认的点
- 确认 eulerpublisher 包中其他应用的测试脚本是否也存在同样的 CRLF 换行符问题（如 `bwa_test.sh` 之外还有哪些 `*_test.sh` 脚本）。
- 确认 CI runner 上 eulerpublisher 包的版本和安装来源，以定位换行符混入的根环节。
- 若该基础设施问题短期内无法修复，可考虑临时绕过：重跑 CI 时跳过 [Check] 阶段，或手动触发仅构建不测试的流水线。
