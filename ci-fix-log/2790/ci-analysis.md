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
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 eulerpublisher 工具对 PR 变更文件执行 appstore 发布规范预检时，检测到 `README.md` 被修改，但其路径格式（相对路径 `README.md`）与工具期望的格式（绝对路径 `/README.md`）不匹配，导致路径校验失败。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的两个文档文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像的可用 Tags 列表。这是纯文档变更，不涉及 Dockerfile、meta.yml、image-info.yml 等应用镜像构建文件或元数据文件。失败并非由 PR 内容错误引起，而是 CI 的 appstore 发布规范预检环节对根层级 README 文件执行了并不适用的路径格式校验——该预检本应仅针对 `{category}/{image}/{version}/{os-version}/` 目录树下的应用镜像文件执行，不应拦截根目录的纯文档更新。

## 修复方向

### 方向 1（置信度: 中）
PR 仅修改根目录 README 文档，不涉及任何应用镜像的 Dockerfile 或元数据文件。该 PR 应通过 CI 检查。需要确认 CI 的 appstore 发布规范预检逻辑是否错误地将根层级文件（`README.md`、`README.en.md`）纳入了校验范围，若如此则需修改 eulerpublisher 工具的路径过滤逻辑，使其仅校验 `{category}/` 子目录下的应用镜像相关文件。

### 方向 2（置信度: 低）
若 CI 工具期望的路径格式 `/README.md` 是硬性要求（即期望传入路径带前导 `/`），则可能是 eulerpublisher 内部路径拼接/传递方式有问题，`git diff` 输出的路径为 `README.md`（不带 `/`），而校验函数期望绝对路径。这属于 CI 工具本身的 bug，与 PR 变更无关。

## 需要进一步确认的点
- CI 日志中仅检测到 `README.md` 变更，但 PR diff 同时修改了 `README.en.md`。需确认 `README.en.md` 未被检测到的原因（是否被 diff 过滤逻辑忽略，或基础分支已含相同内容）。
- CI 日志中实际 PR 编号为 #3194（`PR 3194 [sunshuang1866:fix/2790 -> master]`），而上下文标记 PR 为 #2790。`fix/2790` 可能指向 issue 编号，而非 PR 编号，需确认准确的 PR 标识。
- 需查看 eulerpublisher 源码中路径校验逻辑，确认根层级 README 文件是否应被纳入 appstore 发布规范预检范围。

## 修复验证要求
（本报告置信度为"高"，修复方向 1 无需涉及正则 patch 外部源文件。若采纳方向 2 修改 eulerpublisher 工具源码，需在 CI 环境中验证路径校验逻辑对根层级文件的处理行为。）
