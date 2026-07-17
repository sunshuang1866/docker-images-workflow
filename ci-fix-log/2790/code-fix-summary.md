# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error）：eulerpublisher 的 appstore 发布预检工具错误地将根目录 `README.md` 纳入镜像发布路径校验，而根目录文档文件不应参与 appstore 发布规范的路径验证。

## 修改的文件
无。`README.md` 的内容（镜像 Tag 列表更新）是正确的文档维护变更，不存在代码层面的问题。

## 修复逻辑
CI 失败根因位于 `eulerpublisher/update/container/app/update.py:273` 的 appstore 预检逻辑，该检查遍历 PR 中所有变更文件并按镜像发布目录结构进行路径校验。根目录 `README.md` 不属于任何镜像发布条目（不在 `Base/`、`AI/`、`Bigdata/` 等类别子目录下），因此校验失败。

这是 CI 基础设施层面的缺陷——预检工具应在检测到仅包含根目录级文档变更时跳过 appstore 路径校验，或排除已知的非镜像文件（如根目录 `README.md`、`README.en.md`）。PR 作者无法修改 CI 管道配置，此问题需由 CI 维护方在 eulerpublisher 仓库中修复。

## 潜在风险
无。未对源代码做任何修改，不引入任何风险。