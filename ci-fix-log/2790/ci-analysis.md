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
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范校验工具（eulerpublisher）检测到 PR 修改了仓库根目录的 `README.md` 和 `README.en.md`，并对其执行了路径校验。`README.en.md` 的路径不符合 appstore 规范期望（规范期望文件路径为 `/README.md`，而 `README.en.md` 不在预期路径列表中），导致校验失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中"可用镜像的 Tags"列表的内容（更新 latest 标签从 SP2→SP3、新增 25.09 和 SP2 独立条目）。这些是仓库级别的文档内容更新，不应触发 appstore 发布规范预检。但 CI 校验工具对所有变更文件均执行了 appstore 路径校验，导致根级 README 被误判为不符合规范的路径。

**注意**：PR diff 中存在额外问题——`24.03-lts-sp3` 条目出现重复（一行带 `latest` 别名，另一行独立出现），这可能是触发 CI 路径校验异常的因素之一，但 CI 报错信息明确显示为 `[Path Error]` 而非内容重复错误。

## 修复方向

### 方向 1（置信度: 高）
**移除 README 中的重复条目**。PR diff 中新增了重复的 `[24.03-lts-sp3](https://repo.openeuler.org/openEuler-24.03-LTS-SP3/docker_img/)` 独立条目（该标签已作为 `[24.03-lts-sp3, 24.03, latest]` 出现在列表首行），删除重复行。这可能是 CI 规范校验触发异常的直接原因——重复的标签条目导致内部解析异常，最终以路径错误的形式报出。

### 方向 2（置信度: 低）
如果移除重复条目后 CI 仍然失败，则属于 CI 基础设施层面的误判——eulerpublisher 的 appstore 规范校验不应将仓库根目录 README 的变更纳入校验范围。此时需由 CI 维护方调整 eulerpublisher 的校验逻辑，跳过仓库根级 README 的 appstore 路径校验。

## 需要进一步确认的点
1. CI appstore 规范校验工具（eulerpublisher `update.py`）的具体触发逻辑：是否对不同目录层级的 README 文件有区分对待的能力。
2. 同一仓库中其他仅修改根级 README 的历史 PR 是否也曾触发此校验而通过——以此确认是本次 PR 内容问题（重复条目）还是 CI 工具设计如此。
3. `README.en.md` 在 appstore 发布规范中是否有对应的合法路径映射，或者英文 README 理应在 appstore 中以不同路径存放。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次修复不涉及外部源文件的正则 patch。）
