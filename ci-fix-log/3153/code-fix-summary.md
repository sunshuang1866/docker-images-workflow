# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败属于基础设施错误（infra-error）：appstore 发布规范预检脚本 `update.py` 对所有变更文件执行路径校验，但仓库根目录下的 `README.md` 和 `README.en.md` 不匹配任何镜像目录路径模板，被误判为路径错误。

## 修改的文件
无。PR 修改的 `README.md` 和 `README.en.md` 内容正确，不存在任何代码或文档 bug。

## 修复逻辑
分析报告明确指出：**"PR 本身没有代码或构建问题——问题出在 CI 的校验逻辑对纯文档变更缺乏豁免机制。"**

该问题根源在 CI 基础设施脚本 `eulerpublisher/update/container/app/update.py:273`，需在路径校验前增加前置过滤逻辑：若变更文件不在任何镜像场景子目录（`AI/`、`Bigdata/`、`Database/` 等）下，则跳过路径校验。但此文件不在 `pr.changed_files` 范围内，根据修复约束，不可越权修改。

正确的修复应由 CI 维护者在 `update.py` 中增加对仓库根目录文档的豁免逻辑。

## 潜在风险
无。未对任何代码文件做修改。