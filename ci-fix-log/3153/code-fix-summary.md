# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：CI 工具 `update.py` 路径归一化缺陷导致根目录文件 `README.md` 被误判为路径错误，与 PR 变更无实质性关联。

## 修改的文件
无。PR 仅修改了 `README.md` 的文档内容（更新基础镜像可用 tag 列表），不需要对任何源码进行修改。

## 修复逻辑
CI 失败分析报告确认此为 infra-error：
- 根因在 CI 工具 `eulerpublisher/update/container/app/update.py:273`，该工具从 `git diff` 获取相对路径（如 `README.md`）后直接与期望的绝对路径（如 `/README.md`）做字符串比对，导致不匹配误报。
- PR 仅更新了 README 中文档内容，无任何代码或配置变更，与 CI 失败无因果关系。
- 修复应在 `eulerpublisher` 仓库的 `update.py` 中进行路径归一化处理，不在本仓库范围内。

## 潜在风险
无。本次未对源码做任何修改。