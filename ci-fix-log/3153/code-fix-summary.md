# 修复摘要

## 修复的问题
无需代码修改——CI 失败由 CI 基础设施（appstore 预检工具）导致，而非 PR 代码错误。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
此 PR 仅修改了根目录 `README.md`，属于纯文档变更。CI 失败的直接原因是 appstore 上架规范预检工具（`eulerpublisher/update/container/app/update.py`）扫描 PR diff 时将 `README.md` 当作应用镜像条目进行校验，但该文件不在镜像层级目录（如 `Category/Image/Version/`）下，导致路径校验失败。

分析报告明确指出：**该失败由 PR 变更触发，但并非 PR 内容有误，而是 CI 检查工具未对纯文档类 PR 做豁免处理**。PR 内容（更新可用基础镜像 tags 列表）本身完全正确。

由于此问题根源在 CI 工具逻辑（需对纯文档类文件做过滤豁免），而非 PR 变更的 `README.md` 有任何错误，且 `pr.changed_files` 中不包含 CI 工具代码，因此无需对代码仓库做任何修改。

## 潜在风险
无——未修改任何代码。