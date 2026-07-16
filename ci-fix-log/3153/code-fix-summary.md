# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 **infra-error**——CI 编排工具 `eulerpublisher` 的 appstore 发布规范预检工具（`update.py`）存在路径比较缺陷：git diff 输出文件路径为 `README.md`（无前导 `/`），而校验逻辑期望 `/README.md`（带前导 `/`），字符串不匹配导致纯文档 PR 被误判为 appstore 规范违规。PR #3153 仅修改 README 文档内容，代码本身正确无误。

## 修改的文件
无。本 PR 的 `README.md` 无需任何修改。

## 修复逻辑
CI 失败根因位于 `eulerpublisher/update/container/app/update.py`（CI 编排工具仓库，非本仓库），是其路径比较逻辑缺少路径标准化所致。修复应提交到 `eulerpublisher` 仓库，在路径比较时对 git diff 输出和内部期望路径统一添加 `os.path.normpath` 或统一前导 `/` 标准化处理。本仓库（openEuler-docker-images）中的 `README.md` 内容无问题，无需且不应修改。

## 潜在风险
无。不对本仓库任何文件进行修改，不存在风险。