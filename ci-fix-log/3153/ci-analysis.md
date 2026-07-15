# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 变更检测结果（仅识别到 README.md 被修改）：
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检逻辑）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对 PR 变更文件 `README.md` 执行路径校验，判定该文件的路径不符合 appstore 发布规格要求。日志中 `[Path Error] The expected path should be /README.md` 提示预期路径为 `/README.md`，但校验结果为 FAILURE。PR 仅修改了根级 `README.md` 和 `README.en.md` 的内容（更新基础镜像标签列表），未移动文件位置——文件本身即在 `/README.md`，因此 FAILURE 的具体触发条件可能是 CI 工具内部的路径字符串比较不一致（如 `README.md` vs `/README.md`），或根级 README.md 不在 appstore 允许变更的文件白名单内。

### 与 PR 变更的关联
PR 对 `README.md` 和 `README.en.md` 的修改直接触发了 CI 的 appstore 发布规范预检。该预检会扫描 PR diff 中的所有变更文件，并对每个文件进行路径合规性检查。PR 中修改 `README.md` 的行为本身是合法的文档更新，但 CI 校验工具似乎对根级 `README.md` 的路径格式存在校验偏差。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的路径比较逻辑可能存在前导 `/` 的不一致（实际路径为 `README.md`，预期路径为 `/README.md`），导致字符串比较失败。修复方向是在 CI 工具代码中对路径做规范化处理（如统一添加或去除前导 `/`）后再进行比较，或在 appstore 校验白名单中显式豁免根级文档文件（`/README.md`、`/README.en.md` 等非镜像构建产物）。

### 方向 2（置信度: 低）
若 CI 工具的设计意图是防止 README.md 在 appstore 发布流程中被意外修改（即根级 README.md 不应出现在 appstore release PR 中），则修复方向是调整 CI 触发条件，使纯文档修改的 PR（如仅修改 README.md）不触发 appstore 发布规范预检。

## 需要进一步确认的点
1. 需要获取 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的源码（特别是 `[Path Error]` 分支），确认 FAILURE 的具体判定条件。
2. 需要确认 CI 是否应当对仅修改根级 README.md 的 PR 执行 appstore 发布规范预检，还是这类纯文档变更应当跳过此检查。
3. 需要确认 `README.en.md` 是否也在 CI 的 `Difference` 检测结果中被遗漏（仅显示了 `README.md`），这可能是 CI diff 检测的问题。
