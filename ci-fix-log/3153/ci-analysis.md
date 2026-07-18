# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（相近，但不完全匹配）
- 新模式标题: 根级 README 路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 校验工具）
- 失败原因: CI 的 appstore 发布规范校验工具（`update.py`）对 PR 中变更的仓库根级 `README.md` 文件进行了路径校验，该校验本应仅针对应用镜像子目录（`AI/`、`Bigdata/` 等）内的文件。当前 PR 仅修改了根级文档文件，不涉及任何应用镜像的发布，但由于校验工具以 PR 整体 diff 中的变更文件集合为输入，`README.md` 被纳入校验范围，导致路径格式不匹配（diff 返回 `README.md`，校验器期望 `/README.md`）。

### 与 PR 变更的关联
PR #3153 的变更内容完全正确——仅为 `README.md` 和 `README.en.md` 更新基础镜像可用 tag 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，并修正 latest 指向 SP4）。这些文档变更与 CI appstore 校验器的失败无因果关系。失败由 CI 校验工具的设计缺陷导致：它对纯文档类 PR 作出了不必要的 appstore 路径校验，产生了误报。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `eulerpublisher/update/container/app/update.py` 中 `Difference` 变更文件集合的判断逻辑未过滤仓库根级非应用镜像文件（如根级 `README.md`、`README.en.md` 等）。需要在校验前增加文件路径白名单或过滤逻辑：若变更文件位于仓库根目录且不涉及任何应用镜像子目录，则跳过 appstore 发布规范校验，直接通过。此修复在 CI 工具侧，不在本 PR 的 Dockerfile/文档范围内。

### 方向 2（置信度: 低）
若根级路径校验是预期行为（要求根级文件也注册到 appstore 的 image-list.yml 中），则修复方向为：在对应的 image-list.yml 中添加 README.md 条目的路径声明，或将 appstore 校验的路径格式统一为绝对路径（前导 `/`）。但鉴于根级 README 仅为文档说明、与容器镜像发布无直接关系，此方向合理性和必要性存疑。

## 需要进一步确认的点
1. CI 日志仅来自 x86-64 job，需确认 aarch64 job 是否也以相同错误失败，以排除单架构特殊性问题。
2. `eulerpublisher/update/container/app/update.py` 中变更文件过滤逻辑的实际实现——需阅读该文件确认是否已有 "仅校验应用镜像子目录内文件" 的逻辑但存在 bug，还是完全缺少此类过滤。若可访问该 CI 工具源码仓库，应重点审查 `Difference` 处理与路径校验函数的实现。
3. 确认 PR #3153 是否确实只需更新文档，无需触发任何镜像构建。若是，则 CI pipeline 应在 trigger 层面就跳过该 PR 的 appstore 校验 job。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败为 CI 工具自身的路径校验逻辑问题，不涉及对第三方上游源文件的正则 patch。
