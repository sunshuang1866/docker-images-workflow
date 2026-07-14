# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用，为已知模式子类)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 镜像发布规范校验检查）
- 失败原因: CI 的 appstore 发布规范校验工具 `update.py` 在处理 PR diff 时，从 git diff 获取的路径为 `README.md`（无前导 `/`），但内部路径校验逻辑期望的格式为 `/README.md`（带前导 `/`），路径格式不一致导致校验失败。

### 与 PR 变更的关联
PR #3153 **仅修改了两个根层级文档文件**（`README.md` 和 `README.en.md`），更新了基础镜像可用 tags 列表，属于纯粹的文档维护变更。CI 失败是由 CI 工具内部的路径格式处理不一致导致的，**与 PR 的代码/文档内容无关**。

**数据一致性提醒**: CI 日志中 Jenkins job 的触发原因为 "PR 3184 [sunshuang1866:fix/3153 -> master]"，而上下文标注的 PR 编号为 #3153。存在两种可能：(1) PR #3184 是从 `fix/3153` 分支创建的新 PR，包含比 PR #3153 更多的变更，而我们仅拥有 PR #3153 的 diff；(2) 日志标注存在笔误。此不一致降低了本报告的置信度。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑存在 bug：diff 输出模块生成的路径不带前导 `/`（如 `README.md`），而校验模块期望带前导 `/` 的格式（如 `/README.md`）。修复 `update.py` 中的路径处理逻辑，使其在两个模块间使用一致的路径格式（统一加前导 `/` 或统一不加），或者在校验时对根层级文件做特殊处理（根层级文件自然没有前导 `/`）。

### 方向 2（置信度: 低）
该 CI 校验步骤本不应在仅修改根层级 README 文档的 PR 上触发 appstore 发布规范检查。可能是 CI 的触发条件配置有误，导致纯文档更新 PR 也进入了镜像发布规范校验流程。检查 CI pipeline 配置，确保仅涉及镜像目录（`Bigdata/`、`AI/`、`Storage/` 等子目录）文件变更的 PR 才触发 appstore 规范校验。

## 需要进一步确认的点
1. **PR 编号不一致**: CI 日志显示触发的 PR 为 #3184（分支 `fix/3153`），上下文标注为 PR #3153。需要确认两者关系——PR #3184 是否在 PR #3153 基础上追加了其他变更，若如此，当前 diff 不完整，可能遗漏了导致路径校验失败的其他文件变更。
2. **复现验证**: 对仅修改根层级 README 的 PR 重新触发 CI，确认该路径格式错误是否稳定复现，以排除偶发性 infra 问题。
3. **`update.py` 源码逻辑**: 需查阅 `update.py` 第 356 行（diff 计算逻辑）和第 273 行（校验逻辑）的具体实现，确认路径格式不一致的根因是路径拼接 bug 还是校验触发条件过于宽泛。

## 修复验证要求
无。该失败属于 CI 基础设施问题（CI 工具路径校验逻辑缺陷），不涉及正则 patch 外部源文件。
