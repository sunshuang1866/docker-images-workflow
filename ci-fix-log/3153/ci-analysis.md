# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录README路径校验偏差
- 新模式症状关键词: Path Error, expected path should be, README.md, eulerpublisher, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 中 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验步骤）
- 失败原因: CI 的 appstore 发布规范校验工具检测到仓库根目录的 `README.md` 发生了变更，对其进行路径合规性检查时，报告路径错误：期望路径为 `/README.md`，但 `README.md` 本身即位于仓库根目录。该检查所使用的路径比较逻辑（可能为严格字符串匹配含/不含前导斜杠的差异）未能正确识别根目录文件的有效路径，导致误报 `FAILURE`。PR 变更内容为纯文档修改（更新可用镜像 Tags 列表），与构建/测试/代码逻辑无关。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中的可用镜像 Tags 列表（将 `24.03-lts-sp2` 更新为 `24.03-lts-sp4` 并新增 sp3、25.09 条目），未涉及任何 Dockerfile、构建脚本或代码逻辑变更。CI 失败是 eulerpublisher appstore 校验工具对根目录 README 文件的路径判断逻辑问题，与 PR 改动内容无实质关联。

## 修复方向

### 方向 1（置信度: 中）
此失败为 CI 基础设施问题（eulerpublisher 工具的 appstore 路径校验逻辑对根目录 README.md 存在误判），与 PR 代码变更无关。PR 作者无需修改任何文件内容。需由 CI 维护方排查 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑：
- 确认校验逻辑是否对前导斜杠 `/` 的包含与缺失做了严格区分；
- 确认校验逻辑是否应当排除根目录级别、非镜像目录层级的纯文档文件（如 `README.md`）的 appstore 路径检查。

### 方向 2（置信度: 低）
如果 CI 校验逻辑本身不可更改，可尝试在 PR 提交前确认 `README.md` 的文件路径在 CI 校验时是否以特定格式传递（如在 git diff 输出中被表示为无前导斜杠的相对路径，而校验工具期望带 `/` 前缀的绝对路径），但这属于 CI 工具侧的兼容性问题，不应由 PR 作者修改文档内容来规避。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑具体实现，明确 `/README.md` 与 `README.md` 的比较是否因路径格式差异导致误报。
2. 确认 CI 管线中对纯文档 PR（仅修改 README 等非镜像目录文件）是否应跳过 appstore 发布规范检查。
3. 验证同一 CI 流程中 `README.en.md` 是否同样触发了路径错误（日志中仅显示 `README.md` 的检查结果），如未触发，需对比两份文件的路径格式在 CI 工具中的处理差异。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。此 CI 失败为基础设施问题，不涉及对外部源文件的 patch 操作。
