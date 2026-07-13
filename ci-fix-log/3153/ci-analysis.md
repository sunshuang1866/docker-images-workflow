# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根级README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, /README.md, appstore, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本（`update.py`）对 PR 中变更的所有文件执行路径校验，将仓库根级 README 文件（`README.md`、`README.en.md`）也纳入了 image 目录结构规范检查。根级 README 文件不属于任何 image 子目录，无法匹配 appstore 要求的 `{category}/{image}/{version}/{os-version}/README.md` 层级结构，导致路径校验失败。

### 与 PR 变更的关联
PR 仅修改了仓库根级 `README.md` 和 `README.en.md` 的内容（更新基础镜像可用 tag 列表和对应 URL），不涉及任何 image 子目录的 Dockerfile/元数据文件。失败由 CI 预检规则对变更文件的全局路径校验触发，与 PR 变更的内容无关——即使只改动根级 README 的一个字符也会同样失败。这是一个 CI 校验规则对非 image 类型文件缺少豁免机制的 bug。

## 修复方向

### 方向 1（置信度: 高）
CI 预检脚本 `update.py` 的路径校验逻辑需要增加对仓库根级文件的豁免规则。具体来说，应在 `_validate_path`（或等效的路径校验函数）中，对文件路径不在任何 `image-list.yml` 所覆盖的 category 目录下的文件（如 `README.md`、`README.en.md`、`.gitignore` 等根级文件）跳过 appstore 路径规范检查。

### 方向 2（置信度: 中）
如果 CI 预检工具的设计意图是只检查 image 子目录内的文件，那么变更文件列表（`Difference`）的获取逻辑可能需要过滤：仅对位于 `Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/` 等 image category 目录下的文件执行 appstore 路径校验，而非对 PR 的所有变更文件无差别检查。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的具体校验逻辑，确认路径校验函数的实现方式及是否有现成的豁免列表机制。
2. CI 预检工具的设计意图：appstore 路径规范检查是否应覆盖所有变更文件，还是仅覆盖 image 子目录内的文件。
3. 该仓库是否一直存在此问题（即任何修改根级 README 的 PR 都会触发此错误），以及是否有其他根级非 image 文件（如 `.gitignore`、`LICENSE` 等）也会触发同类失败。

## 修复验证要求
若修复方向涉及修改 CI 脚本（`eulerpublisher/update/container/app/update.py`），code-fixer 需确保：
1. 修改后重新触发 CI，确认根级 README 文件的路径校验不再报错。
2. 同时验证 image 子目录内文件的路径校验仍然正常工作（即豁免规则不会错误地跳过应被检查的文件）。
