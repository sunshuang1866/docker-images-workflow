# 修复摘要

## 修复的问题
无需修改 `README.md`。CI 失败是基础设施问题：CI 预检工具 `eulerpublisher/update/container/app/update.py` 对根目录文件（`README.md`）的路径校验存在缺陷，将无害的文档更新误判为不合规。

## 修改的文件
无。`README.md` 内容本身没有问题，本次文档更新（新增基础镜像 tags 条目）是合法的。

## 修复逻辑
分析报告指出根因在 CI 预检工具 `update.py`（不属于本仓库或不在 `pr.changed_files` 范围内）：该工具在扫描变更文件时，将根目录 `README.md` 纳入了 appstore 路径校验逻辑，但未对根级文档文件做白名单过滤，导致路径比较失败（`README.md` vs `/README.md` 前导斜杠不匹配）。

真正的修复应在 `update.py` 中：
- 增加根目录级文档文件的白名单（如 `README.md`、`README.en.md`），使其跳过 appstore 路径结构校验；或
- 在路径比较前对文件路径做规范化处理（补全前导 `/`）。

这些修改超出了本 PR 的文件变更范围（`['README.md']`），需由 CI 基础设施团队处理。

## 潜在风险
无。`README.md` 未被修改，不引入任何风险。