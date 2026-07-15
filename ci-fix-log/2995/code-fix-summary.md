# 修复摘要

## 修复的问题
CI 基础设施错误，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败类型为 `infra-error`，根因是 CI 框架 `eulerpublisher` 内置的测试脚本 `tests/container/app/bwa_test.sh` 使用了 Windows 风格的 CRLF 换行符，导致 shebang 行 `#!/bin/sh` 末尾被附加了不可见的回车符（`^M`），内核尝试定位 `/bin/sh\r` 作为解释器而报错 `bad interpreter: No such file or directory`。

PR 变更（新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及关联元数据文件）的 Docker 镜像构建和推送阶段均已完成且成功，失败发生在构建完成后的 CI 验证测试阶段，与 PR 代码变更无关。

修复应在 `eulerpublisher` 仓库中进行：
1. 将 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF
2. 确保 `.gitattributes` 配置 `*.sh text eol=lf` 以防止再次出现

## 潜在风险
无