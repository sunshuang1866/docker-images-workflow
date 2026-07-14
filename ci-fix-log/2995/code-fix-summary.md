# 修复摘要

## 修复的问题
无需代码修改——此失败为 CI 基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无（PR 代码无需改动）

## 修复逻辑
CI 失败发生在 Docker 镜像构建成功之后的「Check」阶段，由 CI 基础设施自带的测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF）导致 shebang 解析失败（`#!/bin/sh^M`），与本次 PR 变更的 4 个文件（`Dockerfile`、`README.md`、`image-info.yml`、`meta.yml`）均无关联。Docker 镜像构建阶段已完全成功（编译无错误，镜像已构建并推送至 registry）。

修复应由 CI 平台维护者在 `eulerpublisher` 工具包层面进行：将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（如使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理后重新部署）。PR 作者无需修改本仓库代码。

## 潜在风险
无——未对任何源码文件进行修改。