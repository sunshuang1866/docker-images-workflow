# 修复摘要

## 修复的问题
本次 CI 失败为 **infra-error（基础设施错误）**，无需对 PR 代码进行任何修改。

## 修改的文件
无（infra-error，非代码层面问题）

## 修复逻辑
CI 失败发生在 [Check] 阶段，调用 `eulerpublisher` Python 包中预置的测试脚本 `bwa_test.sh` 时，因该脚本使用 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh\r` 被内核解析为不存在的解释器路径 `/bin/sh\r`，报 `bad interpreter`。

Docker 镜像构建阶段完全成功——源码下载、gcc 编译、bwa 二进制产物的安装及依赖清理均正常完成，镜像已成功构建并推送至 registry。

该故障与 PR #2995 变更的 4 个文件（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`）**完全无关**。根因在于 `eulerpublisher` 包中的测试脚本行尾格式问题，需要由 `eulerpublisher` 仓库维护者修复。

## 潜在风险
无（未修改任何代码）