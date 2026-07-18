# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文件路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, update.py, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具在检查 PR 变更文件 `README.md`（仓库根目录）时，期望文件路径为 `/README.md`，但工具内部计算出的文件路径与之不匹配（可能缺少前导 `/` 或相对基准不一致），导致路径校验失败。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，内容变更为更新基础镜像可用 Tags 列表。这是一次纯文档变更，文件位于正确位置 `/README.md`。CI 的 appstore 校验工具未能正确处理根目录级文件的路径比对，产生了误报——该错误与 PR 的代码/内容变更本身无实质关联，属于 CI 工具对根级路径的比对逻辑缺陷。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中 appstore 发布规范校验的路径比对逻辑存在缺陷：当变更文件位于仓库根目录（如 `/README.md`）时，工具计算出的路径与期望路径 `/README.md` 不一致。需排查 `update.py` 中路径标准化或前缀拼接逻辑（第 273 行及附近），确保根级文件路径能正确匹配期望格式（必须带前导 `/`）。

### 方向 2（置信度: 低）
该 appstore 校验本不应适用于根目录的 README.md——根级 README.md 是项目概览文档而非 appstore 镜像制品。可以在校验逻辑中增加跳过规则：若变更文件为根目录的 `README.md` / `README.en.md` 等非镜像制品文件，则直接跳过 appstore 路径/规范校验。

## 需要进一步确认的点
1. 日志中 `update.py` 仅打印了 `Difference: ["README.md"]`，未打印对其他文件的校验结果，无法确认是仅校验了 README.md 还是同时校验了 README.en.md（后者在 PR diff 中也发生了变更但未在 Difference 中列出）。
2. 需在代码库中查看 `eulerpublisher/update/container/app/update.py` 第 222-273 行的路径计算和校验逻辑，确认路径比对的具体实现方式（相对路径基准路径、前导 `/` 处理等）。
3. 确认该 CI 工具对于根目录文件的 appstore 校验是否本意就不应触发（即根目录 README 不是镜像制品的正确存放路径），还是工具本身对根目录路径处理有 bug。

## 修复验证要求
若修复方向为修改 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑，code-fixer 必须在修复后：
1. 在本地模拟 CI 校验环境，使用与日志中相同的 PR diff（仅修改根目录 README.md）验证路径校验通过。
2. 同时验证子目录内合法镜像制品文件（如 `Bigdata/.../README.md`）的路径校验不被破坏。
