# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（update.py）对 PR 中变更的文件进行路径合规检查。PR 仅修改了仓库根目录的 `README.en.md` 和 `README.md` 两个文档文件，这些文件不满足 appstore 镜像发布目录结构的期望路径规范（期望路径格式为 `{category}/{image-name}/{version}/{os-version}/Dockerfile`），导致两项检查均标记为 `FAILURE`。

### 与 PR 变更的关联
直接关联。PR 的 diff 仅修改了 `README.en.md` 和 `README.md` 两个根目录文件的内容（更新可用镜像 Tags 列表），未涉及任何镜像构建文件。CI 的 appstore 发布规范检查在 `update.py:356` 检测到 diff 中包含这两个文件后，执行路径合规校验时发现它们不符合镜像发布规范的路径格式，从而触发失败。该检查本身是 CI 流水线的固定步骤，但此 PR 纯属文档更新，不具备触发该检查的语义必要性。

## 修复方向

### 方向 1（置信度: 高）
PR 仅包含 README 文档内容更新，不涉及镜像构建。如果 CI 规范允许根目录 README 文件在 appstore 检查中放行，需确认该检查是否应对纯文档 PR 跳过；或者 `README.en.md` 文件名是否符合检查预期的命名规范（检查期望 `/README.md`，但实际文件名为 `README.en.md`）。

### 方向 2（置信度: 中）
如果 CI 检查对所有 PR 均强制执行 appstore 路径校验，则根目录 README 变更可能需要通过特定方式标记（如 PR label）来跳过该检查，或 `update.py` 中的路径校验逻辑需将根目录文档文件（`/README.md`、`/README.en.md`）加入白名单放行。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验逻辑：确认 "expected path `/README.md`" 这一预期是从何处推断出来的，以及为何 `README.md` 本身也被标记为 FAILURE（可能与路径比较方式——绝对路径 vs 相对路径——有关）。
- `README.en.md` 是否在项目规范中被要求使用 `README.md` 作为统一文件名。
- 该 appstore 检查是否对根目录文件有特殊的放行逻辑（如 `.claude/` 历史案例中的白名单机制），若有，当前文件是否未被覆盖。
