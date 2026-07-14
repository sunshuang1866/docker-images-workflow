# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），与 PR 代码无关。

## 修改的文件
无。PR 涉及的文件（Dockerfile、README.md、image-info.yml、meta.yml）均正确无误，Docker 镜像构建完全成功。

## 修复逻辑
CI 失败发生在镜像构建之后的 `[Check]` 阶段，根因是 CI 基础设施中 eulerpublisher 包内置的测试脚本 `bwa_test.sh` 包含 Windows 换行符（CRLF），导致 shebang 行被解析为 `/bin/sh^M`，内核报 `bad interpreter: No such file or directory`。该脚本不在 PR 变更范围内，且 Docker 构建所有步骤均正常完成（`#7 DONE 199.0s`，`#8 DONE 8.4s`）。

此问题需由有 CI 基础设施写权限的运维人员修复：对 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换换行格式。

## 潜在风险
无。未对任何源码文件进行修改。