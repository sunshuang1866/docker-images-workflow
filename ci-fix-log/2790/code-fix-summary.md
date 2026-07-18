# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 appstore 发布校验流水线错误触发导致——纯文档 PR（仅修改根目录 `README.md`）被纳入镜像路径校验，属于 CI 基础设施配置问题。

## 修改的文件
无（无需修改 `README.md`）

## 修复逻辑
- CI 分析报告明确指出根因在 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范校验逻辑，以及 CI 流水线的 PR 触发策略。
- PR #2790 仅修改了根目录的 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表），属于纯文档变更，不应触发 appstore 镜像路径校验。
- `README.md` 的内容本身正确无误，不需要修改。
- 实际修复需由 CI 维护方在以下两个层面进行：
  - **CI 流水线层面**：增加 PR 变更文件路径过滤，根目录纯文档变更应跳过 appstore 发布校验。
  - **校验工具层面**：在 `update.py` 的校验逻辑中增加根目录文件的豁免规则。
- 以上修复位置均不在 `pr.changed_files` 允许修改的范围内（仅允许修改 `README.md`），且属于 infra-error 类型。按照指令要求，不做强制代码修改。

## 潜在风险
无（未修改任何代码）