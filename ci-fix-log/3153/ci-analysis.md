# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171 - INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具，非 PR 代码）
- 失败原因: CI 的 appstore 发布规范预检工具在检查 PR diff 中的文件路径时，将 git diff 路径 `README.md`（无前导 `/`）与期望路径 `/README.md`（有前导 `/`）进行字面比较，因前导 `/` 不匹配而判定 FAILURE。实际上该文件确实位于仓库根目录（即 `/README.md`），路径完全正确。

### 与 PR 变更的关联
**与 PR 无关**。此 PR 仅修改了两个 README 文档文件（`README.md`、`README.en.md`）的内容（更新基础镜像可用 tags 列表），未新增、删除、移动或重命名任何文件。`README.md` 自始至终位于仓库根目录 `/README.md`，路径从未改变。CI 失败是 appstore 检查工具的路径比较逻辑缺陷导致的误报（false positive）。

## 修复方向

### 方向 1（置信度: 高）
CI 编排工具 `update.py` 中的路径校验逻辑需要修复：在比对 diff 文件路径与期望路径时，应先统一规范化（添加/去除前导 `/`）后再比较。此为 CI 基础设施工具 bug，Code Fixer **无需对 PR 代码做任何修改**。

### 方向 2（置信度: 低）
若方向 1 确认后 CI 工具本身无 bug，则需检查 PR diff 解析环节：`update.py` 从 git diff 中提取文件路径时可能遗漏了前导 `/`。但鉴于 `git diff --name-only` 的标准输出本身就无前导 `/`，此方向概率极低。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py` 中路径比对的具体实现（特别是第 222-273 行区域的路径规范化逻辑），验证是否为前导 `/` 缺失导致的字面比较失败。
2. 确认此 CI 检查是否为此仓库的必过门禁——若是，需由 CI 平台维护者修复 `update.py` 或在工作流配置中临时跳过此检查以解封 PR。

## 修复验证要求
此失败类型为 `infra-error`，无需 Code Fixer 介入 PR 代码。若 CI 平台维护者决定修复 `update.py`：
- 需在测试环境中用包含 README.md 变更的 PR 触发 CI，验证修复后路径检查通过。
