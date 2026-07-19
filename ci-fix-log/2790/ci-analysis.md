# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用,已有模式匹配)
- 新模式症状关键词: (不适用,已有模式匹配)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `update.py:273` (eulerpublisher appstore 规范检查)
- 失败原因: CI 的 appstore 发布规范预检工具 (`eulerpublisher/update/container/app/update.py`) 检测到 PR 修改了 `README.md`，对其执行了应用镜像路径格式校验，判定该文件路径不符合 appstore 上架规范 `{category}/{image}/{version}/{os-version}/README.md`，报 `[Path Error] The expected path should be /README.md`。

### 与 PR 变更的关联
**PR 直接触发了该失败，但并非 PR 代码有误。** PR #2790 的唯一变更是修改仓库根目录的 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表）。CI diff 检测到 `README.md` 被修改后，appstore 发布规范预检工具自动对其执行了路径校验——将仓库级根 README 误当作应用镜像的 README 提交，从而报出路径格式不匹配。

这是一个 **CI 工具误判（false positive）**：仓库根目录的 `README.md` 是项目主文档，不是某个具体应用镜像的 `image/{version}/{os-version}/README.md`，本不应被纳入 appstore 路径规范检查的范围。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 工具误报，**代码无需修改**。该 PR 仅更新了仓库主 README 中的 Tags 信息，变更内容本身是正确的。需要 CI 维护方处理 eulerpublisher 预检工具的逻辑，使其跳过仓库根级文件的 appstore 路径校验，或要求 PR 不修改根 README 文件。

### 方向 2（置信度: 低，备选）
如果 CI 无法跳过该检查，可将 `README.md` 的修改从该 PR 中移除（仅保留该 PR 原本意图的应用镜像 Dockerfile/元数据变更），另开纯文档 PR 单独提交 README 更新。

## 需要进一步确认的点
- 确认该仓库的 CI appstore 预检是否设计上就会拦截所有命中了 diff 的 `README.md`，还是仅当 diff 涉及 `image-list.yml` 或 `meta.yml` 时才触发路径校验。
- 确认 PR #2790 是否还有其他预期内的应用镜像文件变更被遗漏（仅见 README 变更，若 PR 本意只是更新 README，则可能该 PR 不应在需要过 appstore 检查的分支上提交）。

## 修复验证要求
（无需填写——此失败非代码修复类问题，不存在正则 patch 外部源文件的场景。）
