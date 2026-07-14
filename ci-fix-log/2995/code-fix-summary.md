# 修复摘要

## 修复的问题
无需代码修改。CI 失败是基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
CI 分析报告确认此为 **infra-error**：
1. Docker 镜像构建阶段（`RUN yum -y install ...`、`exporting to image`、`pushing manifest`）**完全成功**，PR 新增的 Dockerfile 无任何问题。
2. 失败发生在构建完成后的 `[Check]` 阶段，由 CI 基础设施 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本触发。
3. 失败根因是该测试脚本使用了 Windows 风格行尾符（CRLF），导致 shebang `#!/bin/sh\r` 无法被内核识别为有效解释器。
4. 报错文件 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 位于 CI runner 上安装的 `eulerpublisher` Python 包路径中，不属于此 PR 的文件变更范围。

修复应在 `eulerpublisher` 仓库侧进行：对 `tests/container/app/bwa_test.sh` 执行 `dos2unix` 转换为 Unix 行尾符（LF）。PR #2995 的代码本身无需任何改动。

## 潜在风险
无