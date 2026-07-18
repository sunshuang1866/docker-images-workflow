# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为 CI 基础设施问题：appstore 发布规范校验工具错误地将根级文档文件（`README.md`）纳入镜像发布路径校验范围，导致路径格式对比失败。

## 修改的文件
- 无。`README.md` 内容本身没有任何问题，无需修改。

## 修复逻辑
CI 失败分析报告明确指出：
- 失败位置在 `eulerpublisher/update/container/app/update.py:273`，属于 CI 基础设施代码，不在本 PR 的变更文件范围（`pr.changed_files = ['README.md']`）内。
- PR #3153 仅修改了 `README.md` 和 `README.en.md` 的文档内容（更新可用基础镜像 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-info.yml 等镜像发布相关文件。
- CI 的 appstore 校验工具在扫描变更文件时，从 `git diff` 获取的路径 `README.md` 不含前导 `/`，而工具内部期望 `/README.md`，导致路径对比失败。此外，根级 `README.md` 本就不属于任何镜像分类目录，不应作为 appstore 发布 PR 的校验对象。

真正的修复需要在 `eulerpublisher/update/container/app/update.py` 中增加文件过滤逻辑（跳过非镜像发布文件），或修正路径归一化逻辑。该文件不在当前 PR 的可修改范围内，因此本次不做代码修改。

## 潜在风险
无。`README.md` 未被修改，不会引入任何新问题。CI 基础设施修复需要在 eulerpublisher 仓库中单独完成。