# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 自带测试脚本）
- 失败原因: CI 编排工具 eulerpublisher 内置的 bwa 镜像测试脚本 `bwa_test.sh` 含有 Windows 风格 CRLF 行尾（`\r\n`），其 shebang 行 `#!/bin/sh\r` 被系统解析为查找名为 `/bin/sh\r` 的解释器（含回车符），导致 `bad interpreter: No such file or directory` 错误。Docker 镜像的构建、导出和推送均已成功完成（日志中 `[Build] finished`、`[Push] finished`），失败仅发生在 eulerpublisher 的 `[Check]` 测试执行阶段。

### 与 PR 变更的关联
**与 PR 变更无关**。此次 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（19 行全新 Dockerfile）、更新了 README.md、image-info.yml 和 meta.yml，均为纯文本文件，不涉及任何测试脚本。Dockerfile 中的 `make -j "$(nproc)"` 使用了正确的 `$()` 命令替换语法，实际构建日志显示 bwa 编译完全成功（所有 36 个 `.c` 文件编译通过，`ar` 和 `gcc` 链接均成功）。失败根因是 CI 编排工具 eulerpublisher 安装包中 `bwa_test.sh` 的 CRLF 行尾问题，属于 CI 基础设施缺陷，Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
CI 运维侧修复：在 CI 节点的 eulerpublisher 安装过程中，对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换行尾，确保 shebang 行不含回车符。此为 CI 基础设施问题，不涉及 Dockerfile 或任何 PR 代码的修改。

## 需要进一步确认的点
- 确认 eulerpublisher 测试脚本 `bwa_test.sh` 的来源（是否从 Git 仓库检出时因 `core.autocrlf` 配置引入了 CRLF 转换）
- 排查同批其他镜像（如本次 CI run 中同时构建的其他 HPC 镜像）是否也因同一 `bwa_test.sh` 脚本触发相同的 Check 阶段失败
- 若 CI 平台支持，可考虑在 eulerpublisher 测试脚本调用前统一做 `dos2unix` 预处理，从根本上杜绝 CRLF 引发的 shebang 问题
