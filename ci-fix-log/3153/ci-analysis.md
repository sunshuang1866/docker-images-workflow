# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| Check Items |                     Description                     | Check Result |
|-------------|-----------------------------------------------------|--------------|
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 规格校验工具）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 修改了仓库根目录的 `README.md`，并将其作为 appstore 镜像 README 进行路径合规性校验。由于根 `README.md` 位于仓库根层级（`/README.md`），不符合 appstore 镜像 README 所需的特定目录路径格式（通常为 `{category}/{image}/{version}/{os-version}/README.md` 或类似结构），校验失败。

### 与 PR 变更的关联
本轮 PR 仅修改了两个文档文件——`README.md` 和 `README.en.md`——更新了 openEuler 基础镜像可用 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，修正 24.03-lts-sp2 的链接 URL）。PR 不涉及任何 Dockerfile、meta.yml、image-info.yml 或应用镜像目录的变更。

CI 失败由 PR 变更的文件列表触发——`update.py` 扫描到 `README.md` 被修改后，将其纳入 appstore 发布规范校验流程。根 `README.md` 是仓库级别的文档，不是任何应用镜像的 README，本不应受 appstore 路径规则约束。因此该失败与 PR 的具体内容变更（Tag 列表更新）无直接因果关系，属于 CI 工具对非镜像文件的误检。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 规格校验工具（`eulerpublisher/update/container/app/update.py`）在扫描 PR diff 时，应将仓库根目录的 `README.md` 和 `README.en.md` 加入忽略列表（skip list），不对其进行 appstore 镜像路径校验。需在 `update.py` 的文件过滤逻辑中增加判断：若文件路径为根层级 `README.md` / `README.en.md`，则跳过 appstore 规范检查。此修复位于 CI 工具代码侧，不在本仓库范围内。

### 方向 2（置信度: 中）
当 PR 仅包含根层级的文档文件变更且不涉及任何 `image-list.yml` 或 `meta.yml` 时，CI 应不触发 appstore 发布规范预检（或预检直接返回通过）。需要在 CI pipeline 的触发条件中加入变更类型判断，文档-only 的 PR 免除 appstore 路径校验。

## 需要进一步确认的点
1. CI 日志中触发构建的 upstream job 引用的是 "PR 3184 [sunshuang1866:fix/3153 → master]"，而非上下文中的 PR #3153。需确认当前提供的日志是否与目标 PR #3153 对应，还是来自另一个相关 PR。
2. 需查看 `eulerpublisher/update/container/app/update.py` 中第 222-273 行的具体校验逻辑，确认文件路径的判断条件和失败判定规则，以验证上述根因推断是否准确。
3. 需确认仓库根 `README.md` 是否在 appstore 上架流程中有特殊用途（如作为基础镜像信息的展示源），若有，则可能需让 `README.md` 同时满足 appstore 的路径/内容规范。

## 修复验证要求
本报告诊断为 CI 工具误检（置信度: 中），修复方向指向 CI 工具侧（`update.py`）的文件过滤逻辑。若 code-fixer 选择修复 CI 校验代码，需验证：
1. 确认 `update.py` 文件中第 273 行附近错误报告函数的具体触发条件。
2. 在修改后，需通过一个仅变更根 README.md 的测试 PR 验证 appstore 预检是否被正确跳过。
