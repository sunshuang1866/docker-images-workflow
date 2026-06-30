# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具对仓库根目录下的 `README.md` 和 `README.en.md` 文档变更执行了应用镜像路径校验。这两个文件是仓库级文档（非应用镜像的 README），不应被 appstore 校验逻辑管辖，但校验工具仍然将它们纳入检查范围并报告 `[Path Error]`。更值得注意的是，`README.md` 本身位于仓库根目录（路径即 `/README.md`），与期望路径 `/README.md` 完全一致，却仍被标记为 FAILURE，这表明校验工具对该文件的路径判断存在逻辑缺陷。

### 与 PR 变更的关联
**与 PR 变更无关——非本次 diff 引入的问题。** 本次 PR 仅修改了两个 README 文件的文档内容（更新 supported tags 列表），未新增或删除任何文件，未修改任何 CI 配置或校验脚本。CI appstore 预检工具对仓库根目录文档文件的校验行为是独立于此次 diff 的既定行为（或 CI 工具 bug），无论 diff 内容如何都会触发相同的错误。

## 修复方向

### 方向 1（置信度: 高）
**CI appstore 预检工具应排除仓库根目录级文档文件。** 校验脚本 `update.py` 在比对 git diff 获取变更文件列表后，应将仓库根目录的 `README.md` 和 `README.en.md` 从 appstore 规范检查范围中排除——这两个文件是仓库整体文档，不属于任何应用镜像的元数据，不应受应用镜像路径规范约束。同时，`README.md` 路径与期望路径一致却仍报 FAILURE 的 bug 也需要修复。

### 方向 2（置信度: 中）
**若 CI 工具不可修改，考虑将 README 变更与其他变更分开提交。** 但考虑到同一路径的 `README.md` 也报错，此方向无法解决问题。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中变更文件筛选逻辑的具体实现——确认为何仓库根目录的 `README.md` 会被纳入 appstore 检查范围
- `README.md` 路径与期望路径 `/README.md` 一致却仍报 FAILURE 的原因——是否为路径标准化（如相对路径 vs 绝对路径）或字符串匹配中的实现缺陷
- 此 CI 预检步骤是否为新增或最近变更，此前是否有同类 PR（仅修改根文档）通过的历史记录

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——修复方向不涉及 patch 第三方/上游源文件）
