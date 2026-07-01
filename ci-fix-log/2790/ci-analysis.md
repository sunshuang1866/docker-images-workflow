# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（相关变体）
- 新模式标题: Appstore README 路径校验
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.en.md, update.py

## 根因分析

### 直接错误
```
2026-06-29 15:21:37,042-...-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-29 15:21:41,552-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 变更了 `README.en.md`，该文件不在 appstore 预期的可变更文件列表（仅 `/README.md`）中，导致路径校验失败。同时 `README.md` 也被标记为 FAILURE，可能是因为工具在检测到任一文件违规时，会将所有变更文件一并报告为失败。

### 与 PR 变更的关联
PR 对根目录的 `README.md` 和 `README.en.md` 进行了镜像 tag 列表更新（添加 24.03-lts-sp3、25.09 等新版本，重新排序条目）。这些变更是纯文档更新，不涉及任何 Docker 镜像构建文件。CI 的 appstore 预检流程是针对镜像发布 PR 设计的，对于仅修改 README 文件的 PR 没有做豁免处理，导致被误拦。但 `README.en.md` 确实不在 appstore 规范允许变更的路径范围内——appstore 规范仅期望变更 `/README.md`（中文 README）。

## 修复方向

### 方向 1（置信度: 高）
从 PR 中移除对 `README.en.md` 的修改，仅保留 `README.md` 的变更。因为 appstore 校验预期路径仅为 `/README.md`，同时变更英文 README 会触发路径错误。

### 方向 2（置信度: 中）
如果英文 README 也必须同步更新，需要确认 CI 工具 `eulerpublisher/update/container/app/update.py` 是否支持将 `README.en.md` 加入允许列表。若支持，可在 PR 中一并修改 CI 配置或允许清单；若不支持，则需分 PR 提交（一个 PR 仅改中文 README 通过 appstore 检查，另一个 PR 改英文 README）。

## 需要进一步确认的点
- CI appstore 预检工具为何对 `README.md` 本身也标记 FAILURE（路径 `/README.md` 与期望一致却未通过），需要查看 `update.py` 源码确认具体校验逻辑。
- 确认 appstore 规范是否明确禁止修改 `README.en.md`，以及纯文档变更 PR 是否应有豁免机制。
- 确认本次 PR 的 README 变更内容自身是否有格式或链接问题（如 24.03-lts-sp3 在 diff 中出现了两次，一次绑定 latest 标签，一次独立列出，是否存在重复条目）。

## 修复验证要求
code-fixer 在修复前需确认 `eulerpublisher/update/container/app/update.py` 中路径白名单的具体逻辑，明确 `/README.md` 是否为唯一允许的根目录文件路径。若修复方向为移除 `README.en.md` 变更，提交前需确认上游源文件中未残留对该文件的引用。
