# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089 - [line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检（由 `update.py` 执行）检测到 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文档文件。该预检工具期望 PR 变更位于合法的 appstore 镜像发布目录结构下（如 `Category/ImageName/version/os-version/Dockerfile`），根级 README 文件不在其允许的路径白名单中，因此被判定为 `[Path Error]`。

### 与 PR 变更的关联
PR 的改动**直接触发**了此失败。本次 PR 仅包含两个根级 README 文件的内容更新（修改支持的 Tags 列表，新增 `24.03-lts-sp3`、`25.09` 等条目），无任何 Dockerfile、meta.yml 或 image-info.yml 等 appstore 镜像发布相关文件变更。CI 的 eulerpublisher 预检工具对所有 PR 统一执行 appstore 发布规范检查，纯文档类 PR 的根级文件变更因此被误报为路径错误。

## 修复方向

### 方向 1（置信度: 高）
这是 CI appstore 预检工具对纯文档 PR 的**误报**。PR 本身的内容（更新 README 中的 Tags 列表）是正确的，无需修改 PR 代码。如果此 PR 仍需通过 CI 合并，需要在 CI 流水线配置中为纯文档类 PR（仅修改 `README.md`、`README.en.md` 等根级文档文件，无 Dockerfile 变更）添加跳过 appstore 发布规范检查的逻辑，或由管理员手动豁免该检查后合并。

### 方向 2（置信度: 中）
如果 CI 要求所有 PR 无论内容都必须通过 appstore 预检，可考虑将 README 的 Tags 更新放入某个合法的 appstore 子目录路径下（但这不符合 README 文件应有的根级位置，不推荐）。

## 需要进一步确认的点
- 确认 CI 流水线是否对纯文档类 PR 有豁免机制；如果没有，需确认是否需要添加一条规则：当 PR 仅修改根级 `.md` 文件（无 Dockerfile、meta.yml、image-info.yml 等）时，跳过 appstore 发布规范预检。
- 确认 PR 触发方式是否正确——日志显示 "PR 2809 [sunshuang1866:fix/2790 -> master]"，与上下文 PR #2790 不一致，确认是否存在 PR 编号混淆或分支映射问题。
