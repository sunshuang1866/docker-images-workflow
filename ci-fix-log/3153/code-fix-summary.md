# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 `infra-error`，根因为 CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 发布预检逻辑将根目录文档文件 `README.md` 纳入了镜像路径规范校验范围，而该文件是项目级文档，非 appstore 镜像条目，不应受此规则约束。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了 `README.md` 和 `README.en.md`（根目录级别），变更内容为更新基础镜像的可用 tag 列表，属于纯粹的文档更新。CI 失败由外部 CI 工具 (`update.py`) 的检测逻辑缺陷导致——该工具将所有被修改的文件都纳入 appstore 镜像路径检查，未过滤根目录非镜像路径下的文档文件。此问题需在 CI 工具侧修复，PR 代码本身无需改动。

## 潜在风险
无