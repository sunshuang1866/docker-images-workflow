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
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

```
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检（`update.py`）对 PR 变更文件进行路径校验，要求变更文件必须匹配 `/README.md` 期望路径。PR 变更了两个根目录文件——`README.en.md` 和 `README.md`。`README.en.md` 与期望路径 `/README.md` 不匹配；`README.md` 虽然文件名正确，但同样被标记为 FAILURE（原因不明确：可能是路径表示缺少前导 `/`、或 CI 检查器代码存在对比逻辑缺陷）。

### 与 PR 变更的关联
- PR 仅修改了根目录的 `README.md` 和 `README.en.md`，更新基础镜像可用 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`，并调整 latest 指向）。这些变更属于纯文档更新，不含任何 Dockerfile 或镜像构建逻辑变更。
- CI appstore 发布规范预检在检测到 PR diff 中包含根目录文件变更后，对其执行路径校验。该预检逻辑似乎未对纯文档 PR 做豁免处理，导致即便变更完全合法，仍被标记为"路径错误"而阻断构建。
- 此失败与 PR 内容高度关联，但根因在 CI 检查器（非 PR 代码本身有误）。

## 修复方向

### 方向 1（置信度: 中）
PR 中 `README.en.md` 触发了路径校验失败。如果 CI 规范不允许根目录存在 `README.en.md` 的变更（或要求其路径格式与 `README.md` 完全一致），可考虑将 `README.en.md` 的变更内容合并到 `README.md` 中，或删除 `README.en.md` 的变更，仅保留 `README.md` 的修改。

### 方向 2（置信度: 低）
`README.md` 本身也被标记失败，怀疑 CI 检查器 `update.py` 的路径比较逻辑存在缺陷（如路径缺少前导 `/` 导致字符串不匹配）。如果排除 `README.en.md` 后 `README.md` 仍失败，则问题在 CI 工具侧，需确认并修复 `update.py` 中根目录文件的路径比较逻辑。

## 需要进一步确认的点
1. CI appstore 规范是否明确允许根目录下存在 `README.en.md` 文件（或仅允许 `README.md`）。需查阅 `eulerpublisher/update/container/app/update.py` 中的路径白名单/检验逻辑。
2. `README.md` 被标记为 FAILURE 的具体原因——是路径缺少前导 `/` 导致字符串比较失败，还是 CI 检查器有其他隐藏校验条件。
3. 如果纯文档 PR（不含镜像构建变更）本身不需要通过 appstore 预检，需确认 `update.py` 是否应该在检测到无 Dockerfile 变更时提前跳过该检查。
