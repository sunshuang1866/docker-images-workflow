# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - update.py[line:356] - INFO: Difference: [ "README.md" ]
2026-07-14 11:28:17,832 - update.py[line:222] - INFO: Clone ... successfully.
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）检测到 PR 变更了 `README.md`，对其执行路径校验时失败。校验工具报告 `Path Error`，声称期望路径为 `/README.md`。鉴于 `README.md` 实际路径即为仓库根目录 `/README.md`，路径应该匹配——但校验仍判定为 FAILURE，说明该校验工具在处理仓库根级 README 变更时存在逻辑问题（可能将根级 README 误纳入应用镜像级别的路径规范检查，或存在路径字符串严格比对 bug）。

### 与 PR 变更的关联
PR #3153 仅修改了两个文件——`README.md` 和 `README.en.md`（中英文根级 README），更新了基础镜像的可用 Tag 列表。这是一次**纯粹的文档更新**，不涉及任何 Dockerfile、镜像构建逻辑或 CI 配置变更。失败由 CI 的 appstore 发布规范预检工具触发，与 PR 的文档内容变更**直接相关**（若 PR 不修改 README.md 则不会触发该校验），但失败的实质原因是 CI 工具对根级 README 的路径校验逻辑存在缺陷，而非 PR 内容有误。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 中负责 README 路径校验的逻辑需要增加对仓库根级 README（`/README.md`、`/README.en.md`）的豁免处理。参考历史模式中 `.claude/agents/README.md` 路径校验问题（同样属于 CI 路径规范校验误判），在校验模块中区分「应用镜像级 README」（位于场景子目录下）与「仓库根级 README」（位于根目录），仅对前者执行路径规范校验。

### 方向 2（置信度: 低）（如方向 1 不适用）
如果 CI 工具的报错信息具有误导性（`Path Error` 实际并非指路径字面不匹配，而是指根级 README 变更未关联任何 `image-list.yml` 中的镜像条目），则修复方向为：在 CI 校验逻辑中增加对「纯文档变更 PR」的识别，当 PR diff 中仅包含根级 `.md` 文件时跳过 appstore 发布规范预检。

## 需要进一步确认的点
1. 查看 `eulerpublisher/update/container/app/update.py` 中 `line:273` 附近和 `line:356` 的差异检测与校验逻辑，确认 README 路径校验的具体实现（是字符串比对还是目录结构遍历），以精准定位为何 `/README.md` 的路径会被判定为不匹配。
2. 确认该 CI 项目历史上根级 README 变更是否均能通过此校验——若之前根级 README 变更未触发过此错误，则可能是 CI 工具版本升级引入了该回归。
3. 确认 `update.py` 报告的 `Difference: [ "README.md" ]` 中是否应同时包含 `README.en.md`——PR diff 明确同时修改了两个文件，但 CI 仅检测到 `README.md`，需排查 diff 解析是否遗漏了变更文件。

## 修复验证要求
（本报告为诊断，不提供代码修改方案。）
