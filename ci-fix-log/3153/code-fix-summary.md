# 修复摘要

## 修复的问题
无需代码修改 — 本次 CI 失败为 infra-error（CI 基础设施问题），与 PR #3153 的文档变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败由 CI 编排工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑缺陷触发：该工具期望变更文件路径以 `/` 开头（如 `/README.md`），而 git diff 输出的是相对路径（`README.md`），两者不匹配导致校验误报。PR #3153 仅修改了仓库根目录下 `README.md` 和 `README.en.md` 的文档内容（更新基础镜像可用 Tags 列表），属于纯文档变更，未修改任何 Dockerfile、构建脚本或元数据文件。

由于这是 CI 基础设施工具 `eulerpublisher` 的缺陷，且该工具不在当前源码仓库内，无法从本仓库侧进行代码修复。需将问题提报给 CI 工具维护方，在 `update.py` 第 273 行附近的路径校验逻辑中增加路径标准化处理（如统一去除前导 `/`），或对仓库根级纯文档文件（如 `README.md`）进行豁免过滤。

## 潜在风险
无（未对源码仓库做任何修改）