# 修复摘要

## 修复的问题
无需代码修复。CI 失败是基础设施问题（infra-error），由 `eulerpublisher` 包内置测试脚本 `bwa_test.sh` 的 CRLF 换行符导致，与 PR #2995 的 Dockerfile 代码变更无关。

## 修改的文件
无（CI 基础设施缺陷，非本仓库代码问题）

## 修复逻辑
CI 日志显示 Docker 镜像构建和推送均已完成（`[Build] finished`、`[Push] finished`），失败发生在检查/测试阶段。`bwa_test.sh` 文件使用了 Windows 风格的 CRLF 换行符，导致 shebang `#!/bin/sh` 被解析为 `#!/bin/sh\r`，Linux 内核无法找到解释器，报 `bad interpreter`。该脚本位于 `eulerpublisher` 软件包安装路径，需要在 eulerpublisher 源码仓库中修复该文件的换行符格式后重新发布，本 PR 无需且不应做任何代码修改。

## 潜在风险
无