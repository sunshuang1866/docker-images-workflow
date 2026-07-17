# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 `eulerpublisher` 包内置测试脚本 `bwa_test.sh` 的 CRLF 换行符导致。

## 修改的文件
无（无需修改 PR 文件）

## 修复逻辑
CI 分析报告明确指出：PR 的 Dockerfile 构建和镜像推送均已完全成功，失败仅发生在 CI 自身的 [Check] 后置测试阶段。`bwa_test.sh` 位于 `eulerpublisher` Python 包安装目录下（`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`），不是 PR 引入的文件。该脚本使用 Windows 换行符（CRLF），导致 shell 将 `/bin/sh\r` 识别为解释器路径而报错。

此问题需要 CI 运维人员修正 `eulerpublisher` 包中的测试脚本文件格式（将 CRLF 转换为 LF），不属于 Code Fixer 或 PR 作者的修复范围。

## 潜在风险
无