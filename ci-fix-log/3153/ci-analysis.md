# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（变体）
- 新模式标题: CI路径校验误报
- 新模式症状关键词: Path Error, expected path, appstore, README.md, 根目录

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-.../update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-07-12 15:33:13,075-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）对所有 PR 变更文件执行路径校验，要求 README 文件遵循应用镜像目录结构（如 `{app}/{version}/{os-version}/README.md`）。本 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 tags 列表），这两个文件属于仓库级文档，不隶属于任何应用镜像目录，因此被校验脚本判定为路径不合规。

### 与 PR 变更的关联
PR 的改动与失败**直接相关但不是代码错误**：本 PR 是一个纯文档更新——将 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表的 `latest` 标签从 `24.03-lts-sp2` 改为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目。这些改动本身完全合法，但触发了 CI 的 appstore 路径校验逻辑，该校验将仓库根目录下的 README 文件也纳入了应用镜像路径规则检查范围。

## 修复方向

### 方向 1（置信度: 中）
CI 校验脚本 `update.py` 的路径检查逻辑未区分仓库级文档与应用镜像文档。需要修改校验逻辑，使其仅对位于应用镜像目录结构内的文件执行 appstore 路径校验，排除仓库根目录及非应用镜像路径下的文件（如 `README.md`、`README.en.md`、`.github/` 下的文件等）。

### 方向 2（置信度: 低）
如果 CI 设计意图确实要求根目录 README 文件也通过 appstore 校验，则需确认 appstore 对根目录下 README 文件的路径规范定义，并调整本 PR 的文件路径以满足该规范。但考虑到 `README.md` 和 `README.en.md` 是仓库的门面文档，移动它们不符合常规仓库布局惯例，此方向可能性较低。

## 需要进一步确认的点
1. CI 校验脚本 `eulerpublisher/update/container/app/update.py` 中是否已有排除非应用镜像路径的逻辑，还是对所有 PR 变更文件进行无差别校验。
2. 历史上是否有其他仅修改仓库根目录文件的 PR 也触发了同样的 appstore 路径校验失败（检查是否有已知豁免清单或白名单机制）。
3. README.md 校验失败的具体比对逻辑——错误信息显示"expected path should be /README.md"，但当前文件已位于 `/README.md`，需确认比较算法细节（是否涉及大小写、换行符、或与 target 分支的差异比较）。
