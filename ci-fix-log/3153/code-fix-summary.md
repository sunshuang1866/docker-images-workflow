# 修复摘要

## 修复的问题
无需修改代码。CI 失败属于基础设施问题（infra-error），PR 修改的 `README.md` 和 `README.en.md` 内容本身没有问题。

## 修改的文件
无。PR 涉及的两个文件 `README.md` 和 `README.en.md` 是纯文档更新（更新基础镜像可用 Tags 列表），内容正确，无需改动。

## 修复逻辑
CI 失败的原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑对所有 PR 变更文件执行统一检查，期望变更文件符合应用镜像的路径规范（如 `{category}/{image-version}/{os-version}/README.md`），但仓库根目录的文档文件（`README.md`、`README.en.md`）不匹配该规范，导致 `[Path Error]` 误报。

此问题的根因在于 CI 校验脚本（`update.py`）未对纯文档类 PR 做豁免处理，而非 PR 修改的文件有任何错误。该脚本不在本次 PR 的变更文件列表中，无法在本次修复范围内修改。

## 潜在风险
需要 CI 维护人员对 `update.py` 的 appstore 路径校验增加白名单机制，将仓库根目录文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等）排除在路径规范检查之外，以避免未来类似纯文档 PR 被误判。