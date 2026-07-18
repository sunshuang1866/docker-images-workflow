# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级README触发appstore路径校验
- 新模式症状关键词: update.py, Path Error, The expected path should be, appstore, README.md, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
2026-07-16 20:34:19,171 - INFO: Difference: [
    "README.md"
]
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检脚本 `update.py` 对 PR 变更文件执行路径校验，`README.md` 的相对路径格式（缺少前导 `/`）与 CI 校验期望的 `/README.md` 绝对路径格式不匹配，导致 FAILURE。

### 与 PR 变更的关联
**与 PR 改动无直接关联。** PR 仅修改了两个根级 README 文件（`README.md` 和 `README.en.md`）中的基础镜像 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，将 latest 从 24.03-lts-sp2 更新为 24.03-lts-sp4）。这是纯粹的文档内容更新，不涉及任何应用镜像或 appstore 发布制品。

失败的根本原因是 CI 的 appstore 发布规范校验流程被全量 PR 触发，无法区分"根级项目文档变更"和"应用镜像文件变更"，导致根级 README.md 被纳入 appstore 路径校验并因路径格式差异被拦截。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线编排层面：排除根级文件（如 `README.md`、`README.en.md`、`LICENSE`、`CONTRIBUTING.md` 等）的 appstore 路径校验，使纯文档 PR 不再触发该检查。此修复位于 CI 编排逻辑中（如 `eulerpublisher` 工具或 Jenkins pipeline 配置），不涉及本仓库 PR 的代码改动。

### 方向 2（置信度: 低）
若 CI 校验工具无法排除根级文件，可在 `README.md` 中补充 appstore 期望的元数据头或标记，使路径检查通过。但此方向可能引入不必要的元数据到项目文档中，非理想方案。

## 需要进一步确认的点
1. `update.py:273` 中路径校验的具体逻辑——是对比 `git diff` 输出的相对路径与预期绝对路径，还是对比文件在仓库中的路径与 appstore 注册路径。
2. CI 编排中是否有按文件路径过滤的机制（如只校验 `AI/`、`Bigdata/` 等场景目录下的变更文件）。需查阅 `eulerpublisher/update/container/app/update.py` 以及对应的 Jenkins pipeline 配置。
3. 确认该 CI 检查是否对所有纯文档 PR（不涉及任何应用镜像）都返回 FAILURE，还是仅本次 PR 特殊触发。
