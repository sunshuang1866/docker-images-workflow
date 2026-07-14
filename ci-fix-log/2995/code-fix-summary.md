# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施缺陷（infra-error），与 PR 变更无关。

## 修改的文件
无（infra-error，无需修改任何 PR 代码）

## 修复逻辑
CI 分析报告指出：[Build] 和 [Push] 阶段均已成功完成，失败仅发生在 [Check] 阶段。根因是 CI 工具链 `eulerpublisher` 安装目录下的 `bwa_test.sh` 测试脚本 shebang 行（`#!/bin/sh`）末尾带有 Windows 换行符（`\r`），导致系统错误地查找解释器 `/bin/sh\r`。此为 CI 基础设施的 CRLF 行尾问题，与本次 PR 新增/修改的 Dockerfile、README.md、image-info.yml、meta.yml 均无任何关联。

修复应在 CI 运维侧进行：对 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换行尾为 LF。

## 潜在风险
无。PR 代码无需改动，不引入任何风险。