# CI 失败分析报告

## 基本信息
- PR: #3184 (from branch `fix/3153`) — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 update.py:356 INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839 update.py:273 ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具在验证 PR 改动文件路径时，将 git diff 输出的 `README.md`（不含前导 `/`）与期望路径 `/README.md`（含前导 `/`）做字符串精确匹配，因缺少路径规范化处理导致比对失败。该 PR 仅修改了位于仓库根目录的 `README.md` 和 `README.en.md`，文件位置本身是正确的。

### 与 PR 变更的关联
**与 PR 代码改动无关。** 该 PR (#3153 的修复分支) 仅更新了 README.md 和 README.en.md 中基础镜像可用 Tags 列表（添加 `24.03-lts-sp4`、`25.09` 等新版本 tag，更新 `latest` 指向），属于纯文档更新。CI 失败是由 eulerpublisher 工具在 appstore 发布规范预检阶段中的路径比对逻辑缺陷引起的，任何修改仓库根目录下 Markdown 文件的 PR 都可能触发同样的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，PR 代码无需修改。应由 CI 维护团队修复 `eulerpublisher/update/container/app/update.py` 中的路径比对逻辑，在比对前对 `git diff` 输出的路径做规范化处理（添加前导 `/` 或移除期望路径中的前导 `/`），使双方使用一致的路径格式进行比对。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 第 351-356 行获取 diff 变更文件列表后，在第 273 行附近进行 appstore 路径校验时，是否对路径格式做了规范化（normalize）处理。
- 确认该 appstore 发布规范检查是否为强制阻塞项——如果仅修改仓库根目录顶层文件（非应用镜像目录下的文件）不应触发此检查。

## 修复验证要求
（不适用——此问题为 CI 工具缺陷，修复不涉及正则 patch 外部源文件。）
