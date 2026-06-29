# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本对 PR 中变更的所有文件进行路径校验。仓库根目录的 `README.md` 和 `README.en.md` 被检测为变更文件后，校验工具认为这些根层级文件不符合 appstore 发布规范要求的路径格式（appstore 期望的路径应与应用镜像目录结构对应，而非仓库根目录的文档文件），导致 `[Path Error]`。

### 与 PR 变更的关联
PR 仅修改了 `README.en.md` 和 `README.md` 的内容（更新了 supported tags 列表），属于纯文档更新。失败并非由 PR 的文档内容变更触发，而是 CI 的 appstore 预检流水线将所有变更文件（包括根目录 README）纳入了 appstore 路径校验范围。根目录 README 文件不应受 appstore 发布规范约束。

这与历史案例 PR #2512 的模式一致——CI appstore 预检将非应用镜像的文档文件（如 `.claude/` 下的 README）进行了路径校验。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 预检脚本（`update.py`）未排除仓库根目录的 README 类文件。需要在预检逻辑中对根层级文档文件（如 `README.md`、`README.en.md`）做豁免处理，使其不进入 appstore 路径校验流程。这与历史 PR #2512 中 `.claude/` 目录 README 文件的处理方式一致。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中文件过滤逻辑的具体实现，确定在哪个阶段可以添加根目录文档文件的豁免规则。
- 确认该 CI 检查是否为 PR #2790 引入的新逻辑，还是已存在的检查规则对本次变更产生了误报。
