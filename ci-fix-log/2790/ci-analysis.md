# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具在路径校验时，将 git diff 产出的相对路径 `README.md` 与期望的绝对路径 `/README.md` 做字符串比对，因缺少前导 `/` 导致路径匹配失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个文档文件（新增 24.03-lts-sp3、25.09 等镜像 tag 条目，更新 latest 标签），不涉及任何 Dockerfile 或构建逻辑变更。CI 在构建/编译阶段未报任何错误——失败发生在 appstore 发布规范的路径预检阶段。该预检工具在提取 git diff 文件列表后，对每个文件校验其路径是否符合 appstore 发布规范，此处因 path 字符串格式不一致（`README.md` vs `/README.md`）产生误报。**PR 的文档变更本身是合法且正确的。**

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范校验逻辑存在路径归一化缺陷：git diff 输出的文件路径为仓库相对路径格式（如 `README.md`），而校验器中的期望路径格式为绝对路径格式（如 `/README.md`）。需在路径比对前统一归一化（去除或添加前导 `/`）。

**此问题与 PR 代码变更无关，属于 CI 基础设施（infra-error），Code Fixer 无需处理 PR 中的 README 文件。**

### 方向 2（置信度: 低）
本次 PR 可能触发了 appstore 发布规范中"纯文档 PR 不允许触发发布流程"的校验规则，但校验工具的错误提示不够精确，给出了误导性的 "Path Error" 信息。若此方向成立，则修复应在 appstore 发布规范的 PR 类型判定逻辑中，而非路径校验中。

## 需要进一步确认的点
1. 查阅 `eulerpublisher` 仓库中 `update/container/app/update.py:273` 附近的路径校验逻辑，确认是否仅为路径格式归一化问题。
2. 确认该 repo 的 appstore 发布规范是否允许纯文档（README 仅更新）类型的 PR 通过预检，或是否需要 PR 至少包含一个 Dockerfile 变更。
3. 若近期有其他纯文档 PR 也遇到了相同错误，可进一步验证该 CI 缺陷的复现性和影响范围。

## 修复验证要求
（不适用——本失败类型为 infra-error，修复对象为 CI 工具而非 PR 代码。）
