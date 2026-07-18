# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI路径归一化缺陷
- 新模式症状关键词: Path Error, expected path, README.md, update.py, appstore

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范校验工具从 `git diff` 获取的变更文件路径为相对路径 `README.md`（无前导 `/`），而路径校验规则期望的是绝对路径 `/README.md`（带前导 `/`），两者字符串比较不匹配，导致根目录 README.md 的纯文档修改被误判为路径错误。PR 仅修改了 `README.md` 和 `README.en.md` 的文档内容，无任何代码或配置变更。

### 与 PR 变更的关联
PR 变更与失败**无实质性关联**。PR 仅更新了 README 中基础镜像可用 tag 列表（新增 sp4、sp3、25.09 等条目），属于纯文档维护。CI 失败由 `update.py` 中路径归一化逻辑的缺陷触发：对于根目录文件，`git diff --name-only` 输出 `README.md`（相对路径），校验逻辑期望 `/README.md`（绝对路径），字符串直接比对导致误报。即使 README.md 内容未发生任何变更，只要被 `git diff` 检测到存在于变更集中，同样会触发此失败。

## 修复方向

### 方向 1（置信度: 中）
在 CI 工具 `update.py` 的路径校验逻辑中，对从 `git diff` 提取的文件路径进行归一化处理：在路径前补齐 `/`（若缺失），使其与期望的绝对路径格式一致，消除相对路径与绝对路径之间的字符串级比对差异。该修复应提交到 `eulerpublisher` 仓库。

### 方向 2（置信度: 低）
若 CI 路径校验逻辑无法直接修改，可在 PR 侧通过触发一次空提交或其他非 README 文件的微小合法变更，使 CI 的 diff 检测绕过对根目录 README 的路径校验。此方向仅为规避手段，不推荐。

## 需要进一步确认的点
1. 需查看 `eulerpublisher/update/container/app/update.py` 第 222-273 行之间的路径校验实现，确认 `README.md` 与 `/README.md` 的比较是否确为字符串直接比对（而非 `os.path` 或 `pathlib` 的语义化路径比较）。
2. 需确认是否存在其他根目录文件（如 `README.en.md`）因同样原因未被检出——日志中 `Difference` 仅列出 `README.md`，但 diff 中同时变更了 `README.en.md`。若后者未被校验，需确认校验工具的文件过滤逻辑。
