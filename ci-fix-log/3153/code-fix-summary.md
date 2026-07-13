# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 `eulerpublisher` 工具错误地对纯文档 PR（根目录 README 文件变更）执行 appstore 发布规范路径校验导致，属于 CI 基础设施配置问题（infra-error），与 PR 代码内容无关。

## 修改的文件
无（CI 基础设施问题，非代码层面可修复）

## 修复逻辑
- CI 的 `eulerpublisher` 工具要求所有 PR 变更文件必须符合 appstore 镜像发布目录路径格式（如 `{Category}/{Image}/{Version}/{OSVersion}/`），但根目录的 `README.md` 和 `README.en.md` 是仓库文档文件，不属于任何 appstore 发布目录。
- PR #3153 仅更新了这两份文档中加入基础镜像可用 tag 列表，内容正确无误，不应触发 appstore 路径校验。
- 该问题需要在 CI 流水线或 `eulerpublisher` 工具层面解决（如对仅修改根目录 `*.md` 文件的 PR 跳过 appstore 路径校验，或为根目录文档文件添加白名单例外），不在本次 PR 的代码范围内。

## 潜在风险
无（未修改任何代码文件）