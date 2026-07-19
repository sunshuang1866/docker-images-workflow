# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无。PR #3153 仅修改 `README.md` 文档内容，不涉及任何应用镜像、构建文件或代码变更。

## 修复逻辑
CI 分析报告明确指出：失败类型为 `infra-error`，根因是 CI 的 appstore 发布规范校验工具（`eulerpublisher/update/container/app/update.py:273`）对根目录 `README.md` 的变更错误地触发了 appstore 路径校验。PR 实际改动为纯文档更新（更新基础镜像可用 Tags 列表），与 appstore 应用镜像发布无关，该校验本不应针对根目录 README 执行。

根据修复原则，infra-error 类失败不应强行修改代码。建议重新触发 CI 运行，或联系 CI 维护团队确认 appstore 校验工具是否需要排除根目录 README 文档变更。

## 潜在风险
无。未对代码做任何修改。