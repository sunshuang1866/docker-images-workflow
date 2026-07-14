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
2026-07-14 11:28:17,839 update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 流水线中的 appstore 发布规范预检工具（`eulerpublisher`）对 PR 变更的根级 `README.md` 触发了路径校验，校验结果为 `[Path Error] The expected path should be /README.md`，判定为 FAILURE。该预检工具本应为应用镜像目录（`Bigdata/`、`AI/` 等）下的 Dockerfile 和元数据文件设计，但对于仅修改根级文档文件（`README.md`、`README.en.md`）的纯文档 PR，同样触发了路径规范检查并误报失败。

### 与 PR 变更的关联
PR 变更仅在 `README.md` 和 `README.en.md` 中更新基础镜像可用 Tags 列表（将 latest 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，补充 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目），不涉及任何 Dockerfile、元数据文件或镜像构建逻辑。变更本身内容正确、格式合法，不会导致任何构建或功能问题。CI 失败由 appstore 预检工具对根级文档文件的路径校验逻辑缺陷引起，与 PR 内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中的 `eulerpublisher` appstore 预检工具需要在文件校验逻辑中排除根级纯文档文件（`README.md`、`README.en.md`、`LICENSE` 等），使其不参与 appstore 发布规范的路径格式检查。该类文件不属于任何应用镜像目录，不应受到 `{image-version}/{os-version}/` 等层级结构的路径约束。

### 方向 2（置信度: 低）
如果 CI 工具不支持快速修改，可尝试在 PR 中判断 CI 是否会因"无文件变更"而跳过该检查——即确认此 PR 的根级文档变更是否可以被 CI 视为无需触发 appstore 检查的 trivial change。但此方向依赖于 CI 流水线配置，不在本 PR 代码控制范围内。

## 需要进一步确认的点
1. 获取 `eulerpublisher/update/container/app/update.py` 第 273 行附近的源码，确认 `[Path Error]` 的触发条件——尤其是文件路径的比对逻辑，以验证根级 `README.md` 是否被错误地当作需校验路径的应用镜像文件处理。
2. 确认 CI 流水线中是否有机制跳过纯文档 PR 的 appstore 预检（如条件判断 `paths-ignore` 或类似）。
3. 确认 `eulerpublisher` 工具的最新版本是否已有对根级文档文件的豁免逻辑。
