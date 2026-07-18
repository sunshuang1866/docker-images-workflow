# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 流水线中的 `eulerpublisher` 工具检测到 PR 修改了仓库根目录的 `README.md`，对其执行 appstore 发布规范路径校验时判定为「路径错误」。CI 预检工具期望变更文件遵循 image 目录下的层级路径结构（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），而仓库根目录的 `README.md` 不属于任何 image 发布路径，因此被校验逻辑拒绝。

### 与 PR 变更的关联
**直接关联**。PR #2790 仅修改了两个文件：
- `README.en.md`：更新了 "Supported Tags" 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，更新 `latest` 指向 SP3）
- `README.md`：对应中文版做了同样的更新

CI 工具在 `update.py:356` 检测到差异文件集为 `["README.md"]`（仅识别了 `README.md`，未识别 `README.en.md`），随后对这些文件进行 appstore 发布规范检查，最终在 `update.py:273` 抛出路径校验失败。该失败并非 README 内容本身有问题，而是 CI 预检工具对根级 README 文件也执行了面向 image 发布目录结构的路径校验，属于工具与 PR 变更范围的不匹配。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中的 `eulerpublisher` appstore 预检工具在扫描 PR 变更文件时，应将仓库根目录的 `README.md` / `README.en.md` 排除在路径校验范围之外，或仅对 `image-list.yml` 中已注册的 image 目录下的文件执行发布规范检查。该修复应在 CI 工具/流水线层面处理，而非在 Dockerfile/源码中修改。

### 方向 2（置信度: 低）
如果 CI 框架无法调整，可考虑将本 PR 的 README 变更与 image 发布相关变更拆分——让 README 文档更新走独立的不带 appstore 检查的 CI 路径（如仅在 master 分支有特定触发条件时才执行 appstore 预检）。

## 需要进一步确认的点

1. CI 日志显示触发来源为 `PR 3194 [sunshuang1866:fix/2790 -> master]`，与上下文给定的 PR #2790 不完全一致，需确认 PR 编号对应关系。
2. `eulerpublisher/update/container/app/update.py` 的路径校验逻辑（第 273 行附近）的具体实现，以确认其是否对所有文件执行校验还是仅对特定路径的文件执行校验。
3. 该 appstore 预检 job 是否对仓库根目录 README 文件的修改做了豁免处理——如果历史上有纯 README 修改的 PR 通过过该检查，则可能是版本升级导致行为变化。
4. `README.en.md` 与 `README.md` 同步修改，但 CI 工具仅检测到 `README.md`——需确认这是预期行为还是工具遗漏了 `.en.md` 后缀文件。
