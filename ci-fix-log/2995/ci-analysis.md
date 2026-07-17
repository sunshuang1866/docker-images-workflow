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
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher` 的内置测试脚本 `bwa_test.sh`（路径 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 内核无法找到名为 `/bin/sh\r` 的解释器，报 `bad interpreter`。Docker 镜像构建和推送（`[Build] finished`、`[Push] finished`）均成功完成，失败仅发生在 CI 的检查/测试阶段。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Docker 镜像构建完全成功（日志中所有编译步骤均无报错，仅有两个 GCC 编译警告 `-Wunused-but-set-variable`，不影响构建结果）。失败根源是 CI 工具 `eulerpublisher` 包内的 `bwa_test.sh` 测试脚本自身存在文件格式问题（CRLF 换行符），属于 CI 基础设施缺陷，与本次 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
将 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件从 CRLF 换行符转换为 LF 换行符。该文件位于 eulerpublisher 软件包安装路径（由 `pip` 或 `setup.py` 安装），需要在 eulerpublisher 源码仓库中修复该文件的换行符格式，然后重新打包发布。Code Fixer **无需对本 PR 的 Dockerfile 做任何修改**，这是一个纯粹的 CI 基础设施问题。

## 需要进一步确认的点
- `bwa_test.sh` 是 eulerpublisher 包中的哪个版本引入的、是否所有版本都有此 CRLF 问题。若该脚本仅在特定版本中存在问题，可考虑在 CI 环境中降级/升级 eulerpublisher 版本作为临时绕过方案。
- 该 CRLF 问题是否影响 eulerpublisher 中其他镜像的测试脚本（如 `*.sh`），如果是则需在 eulerpublisher 源码仓库中进行批量修复。

## 修复验证要求
无需验证。本失败为 infra-error，且与 PR 代码变更完全无关，Code Fixer 无需对本仓库任何文件进行修改。
