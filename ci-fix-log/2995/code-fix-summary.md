# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），与 PR #2995 的代码变更无关。

## 修改的文件
无（不需要修改任何文件）

## 修复逻辑
CI 失败发生在 [Check] 测试阶段，根因是 eulerpublisher CI 工具链中的 `bwa_test.sh` 测试脚本使用了 Windows 换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带 `\r`，操作系统将解释器路径识别为 `/bin/sh\r` 而报 `bad interpreter: No such file or directory` 错误。

PR #2995 的所有变更（Dockerfile、README.md、image-info.yml、meta.yml）与此次失败完全无关：
- Docker 镜像构建成功（依赖安装、源码编译、镜像推送均无异常）
- 失败仅发生在 CI 基础设施的测试脚本执行阶段

修复需由 CI 基础设施维护者在 eulerpublisher 仓库中完成：将 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`）。

## 潜在风险
无。PR 代码本身没有问题，无需修改。