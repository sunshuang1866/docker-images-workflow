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
2026-07-14 15:28:07,685- update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI appstore 发布规范预检工具（`update.py`）对 `README.md` 进行路径校验时，认为实际路径 `README.md` 与期望路径 `/README.md` 不匹配（缺少前导 `/`），判定为路径格式错误。该文件实际位于仓库根目录，路径完全正确，仅格式差异。

### 与 PR 变更的关联
PR 仅修改了 `README.en.md` 和 `README.md` 两个根目录文件的文档内容，更新了 openEuler 可用镜像 Tags（新增 24.03-lts-sp3、25.09 等版本链接，修正 24.03-lts-sp2 的链接）。变更本身正确无误，不包含任何可能导致路径错误的代码改动。CI 失败由 CI 工具的路径格式校验逻辑触发，与 PR 内容无关。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施/校验工具的路径格式匹配问题，非 PR 代码错误。`update.py` 或下游路径校验逻辑在比较文件路径时未统一规范化路径格式（例如一方使用 `README.md`、另一方使用 `/README.md`）。需修复 CI 工具中 `update.py:273` 附近的路径比较逻辑，确保路径格式统一后再比较，或放宽对根目录路径的格式要求。

### 方向 2（置信度: 低）
如果 CI 工具本身无 Bug，另一种可能是 `README.md` 需要在仓库中同时注册/声明在某个元数据文件（如 appstore 发布清单）中，且声明时使用的路径格式需包含前导 `/`。如果存在此类注册机制，补充声明即可。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行及 **第 222 行（`Clone ... successfully`）到第 273 行之间** 的完整路径校验逻辑，确认是简单的字符串不等比较还是存在其他规范化步骤
2. 该 CI job 的历史通过记录：在该 PR 之前，是否曾有仅修改根目录 `README.md` 的 PR 通过同一校验？若之前通过而现在失败，可能是 CI 工具近期升级引入了回归
3. `README.en.md` 同样被 PR 修改但未被 CI 报告路径错误（日志中 `Difference` 仅列出 `README.md`），需确认差异检测逻辑是否遗漏了 `README.en.md`，或 `README.en.md` 不在 appstore 规范校验范围内
