# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `eulerpublisher` 工具的 appstore 发布规范预检对纯文档 PR 的误报（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此为 **infra-error**：PR #2790 仅修改了根目录 `README.md`（更新可用镜像 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-info.yml 等镜像构建/发布文件。CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检逻辑将根目录 README.md 纳入校验范围，但因该 PR 不包含新镜像提交所需的配套文件而错误地将其标记为 FAILURE。

根据分析报告建议，此问题应由 CI 工具维护者调整校验逻辑（增加对仅文档变更 PR 的豁免处理），或由 PR 提交者联系 CI 管理员手动跳过该检查。PR 本身的代码变更（README.md）不存在任何问题，无需代码层面修复。

## 潜在风险
无