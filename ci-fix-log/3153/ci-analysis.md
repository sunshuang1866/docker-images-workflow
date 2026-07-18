# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11 (CI appstore 发布规范路径校验失败)
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范校验工具在扫描变更文件时，对根目录下的 `README.md` 执行路径格式校验，工具内部期望路径以 `/` 开头（如 `/README.md`），但从 `git diff` 获取到的路径 `README.md` 不含前导 `/`，导致路径对比失败。同时，根级 README 文件不在任何镜像分类目录（`Bigdata/`、`AI/` 等）下，本就不应作为 appstore 发布 PR 的校验对象。

### 与 PR 变更的关联

PR 仅修改了两个根级文档文件——`README.md` 和 `README.en.md`，内容更新了可用基础镜像的 Tags 列表和链接（新增 sp2、sp3、sp4、25.09 条目的列表项，并修正了第一条的链接 URL）。**PR 不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的变更**，因此不应触发 appstore 发布规范预检。该失败与 PR 的文档内容变更本身无关，属于 CI 校验工具对文档 PR 的过度拦截。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 发布规范预检应在执行前判断变更文件是否属于镜像发布相关文件（位于 `{category}/{image}/` 子目录下的 Dockerfile / meta.yml / image-info.yml 等）。若 PR 仅修改根级 README 文件或其他非镜像发布文件，应跳过 appstore 规范校验。建议在 `update.py` 的检查入口处增加文件路径白名单/黑名单过滤逻辑。

### 方向 2（置信度: 中）
若 CI 工具的设计意图是允许根级 README 文件通过 appstore 校验，则需修正工具内部的路径对比逻辑，在比较前对双方路径做统一归一化处理（确保两边都加或不加前导 `/`），消除 `README.md` 与 `/README.md` 的误判。

## 需要进一步确认的点
- 无。错误信息和日志足够明确，根因已定位。

## 修复验证要求
- 不涉及正则 patch 外部源文件，无需额外上游验证步骤。
