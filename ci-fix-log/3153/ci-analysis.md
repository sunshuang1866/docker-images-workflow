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
| Check Items  |                     Description                     | Check Result |
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了 `README.en.md` 和 `README.md` 两个仓库根级文档文件，对其进行路径校验后判定不符合 appstore 发布规范要求的预期路径（两者均被判定为路径错误），阻断 CI 流程。

### 与 PR 变更的关联
PR 仅修改了仓库根级的 `README.md` 和 `README.en.md`（更新基础镜像可用 tag 列表），不涉及任何 Dockerfile 或应用镜像文件。CI 的 appstore 发布规范预检对所有变更文件执行路径校验，`README.en.md` 因文件名与预期 `/README.md` 不匹配而失败；`README.md` 虽与预期路径同名但仍被标记为 FAILURE，具体原因需查看 `update.py` 的路径比较逻辑。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检工具对仓库根级 README 文档文件进行了过于严格的路径校验。`update.py` 的路径校验逻辑应将校验范围限定在 appstore 应用镜像目录下的文件，跳过仓库根级的纯文档文件（如 `README.md`、`README.en.md`），或将其加入白名单使其不触发路径错误。

### 方向 2（置信度: 低）
若 `README.en.md` 的文件名后缀 `.en` 导致路径模式匹配失败，可考虑调整校验逻辑中的文件名正则/模式，使其接受带有语言后缀的根级 README 文件。

## 需要进一步确认的点
- `update.py:222-273` 的路径校验逻辑：确认 `README.md`（文件名与预期路径 `/README.md` 一致）为何仍被标记为 FAILURE，可能涉及路径归一化、前缀匹配或 tail 匹配的边界情况
- 确认 CI appstore 发布规范对仓库根级文档（非应用镜像文件）的预期处理策略：这些文件是否本不应该触发该预检
- 确认此前是否有仅含根级文档修改的 PR 通过该预检（判断是否为回归问题）
