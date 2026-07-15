# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 CI 运行节点上 eulerpublisher 包中的 `bwa_test.sh` 测试脚本包含 Windows CRLF 行尾符（`\r`），导致 shebang 行被解析为 `/bin/sh\r`，系统找不到该解释器而报 "bad interpreter: No such file or directory"。

该问题：
1. 与 PR #2995 的代码变更完全无关（PR 仅新增 Dockerfile 及配套元数据文件）
2. Docker 镜像构建和推送均成功完成
3. 失败发生在 CI 后处理阶段（`[Check]`），由 eulerpublisher 测试工具包自身的问题引发

应由 CI 基础设施维护者对该节点上的 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 去除回车符后重新部署。

## 潜在风险
无