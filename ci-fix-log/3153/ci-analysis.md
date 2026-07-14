# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文档被appstore误校验
- 新模式症状关键词: Path Error, The expected path should be, README.en.md, README.md, appstore, eulerpublisher, update.py

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211 - INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-07-12 15:33:13,075 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对所有 PR 变更文件执行路径校验，但该工具设计目标是校验应用镜像目录结构（如 `{category}/{app}/{version}/{os-version}/...`）下的文件。本次 PR 仅修改仓库根目录的两个 README 文件（`README.md`、`README.en.md`），它们不属于任何应用镜像目录，因此被判定为路径不合规。
  - `README.en.md`：appstore 发布规范预期仓库根目录仅存在 `README.md`（中文版），英文版 `README.en.md` 被标记为"期望路径应为 /README.md"。
  - `README.md`：虽然该文件确实位于根目录 `/README.md`，但校验工具仍报告路径错误。日志证据不足以确定为何同名同位置文件仍然 FAIL，可能原因是校验工具对文件的绝对路径/相对路径表示存在不匹配，或其内部校验逻辑对非应用镜像文件一律报错（错误描述可能为固定模板）。

### 与 PR 变更的关联
- PR 变更内容与 CI 失败**无直接因果关系**。PR 仅更新了两个根级 README 中的基础镜像 Tag 列表（将 latest 关联从 `24.03-lts-sp2` 改为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09` 等条目），不涉及任何应用镜像 Dockerfile、meta.yml 或 image-list.yml。
- CI 失败的根本原因是 appstore 校验管线对所有 PR 统一执行路径检查，而该检查不适用纯文档类 PR。

## 修复方向

### 方向 1（置信度: 中）
CI 管线需要按 PR 改动范围分流：若 PR 仅修改根级文档文件（`README.md`、`README.en.md`、`LICENSE` 等），应跳过 appstore 路径校验步骤。需在 CI 编排层（trigger job）或 `update.py` 中添加早期退出逻辑。

### 方向 2（置信度: 低）
若 appstore 发版流程**必须**校验根级文件，则需在 `update.py` 的路径校验逻辑中将根级 `README.md` 和 `README.en.md` 加入白名单，或在路径匹配规则中补充对根级文档文件的容错处理。

## 需要进一步确认的点
- `update.py` 中路径校验的具体逻辑（行 222–273 区域）：确认其校验对象是否包含根级非应用镜像文件，以及"expected path should be /README.md" 的错误模板是否为硬编码默认值。
- `README.md` 本身路径与期望路径 `/README.md` 一致却仍报 FAIL 的原因（是路径表示格式问题还是校验逻辑 bug）——当前日志不足以定位该行为。

## 修复验证要求
不涉及正则 patch 外部源文件，无需验证步骤。
