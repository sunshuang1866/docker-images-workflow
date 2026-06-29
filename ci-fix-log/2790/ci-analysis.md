# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11（变体）
- 新模式标题: (N/A — 匹配已有模式)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验脚本 `update.py` 对 PR 中变更的全部文件进行路径格式校验，根级文档文件 `README.md` / `README.en.md` 被纳入 appstore 镜像目录约定（`{image-version}/{os-version}/Dockerfile` 层级结构）的校验范围，但这些文件原本就不在应用镜像目录下，无需满足该约定，属于 CI 管线的误报（false positive）。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中版本 Tag 列表的描述性文字（将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）。CI 失败**并非由 PR 的内容变更引起**——即使 README 内容不改动，只要这两个文件出现在 PR 的变更列表中，appstore 路径校验就会将它们标记为不符合镜像目录规范。问题根源是 CI 校验逻辑未排除仓库根目录的文档文件。

## 修复方向

### 方向 1（置信度: 高）
在 CI 校验脚本 `eulerpublisher/update/container/app/update.py` 的 diff 检测阶段，过滤掉仓库根目录的非镜像文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等），使其不被纳入 appstore 发布规范的路径校验范围。校验应仅针对位于应用镜像目录树（`Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`）下的文件。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中 diff 文件过滤逻辑的具体实现（确认是在哪个方法中获取 diff 文件列表，以及 is-image-file 的判断条件）。
- 仓库根目录是否还有其他非镜像文档文件（如 `CHANGELOG.md`、`SECURITY.md`）也需要被排除，需要查阅完整的白/黑名单规则。
