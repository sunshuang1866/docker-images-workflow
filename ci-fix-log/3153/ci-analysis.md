# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 校验工具）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）在扫描 PR 变更文件时，对仓库根目录的 `README.md` 产生路径校验误报——该文件的实际路径 `README.md`（或 `/README.md`）即为项目主文档所在位置，但校验器仍报告 `[Path Error]`，判定为路径不符合预期。

### 与 PR 变更的关联
PR 仅包含两类纯文档变更：
1. `README.en.md`（根目录）— 更新英文 README 中的基础镜像可用 Tags 列表
2. `README.md`（根目录）— 更新中文 README 中的基础镜像可用 Tags 列表

这两处修改均不涉及任何应用镜像 Dockerfile、meta.yml、image-info.yml 或 image-list.yml。CI 的 appstore 发布规范预检是针对所有 PR 变更文件运行的通用检查，但将项目根目录的 `README.md`（项目自身文档）误当作需要符合 appstore 发布路径规范的应用镜像 README 来校验，导致路径校验失败。

**该失败并非 PR 代码变更本身的问题。**

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检工具应排除仓库根目录非应用镜像文件的路径检查。具体而言，`update.py` 在扫描 PR diff 时，对于位于仓库根目录且不属于任何应用镜像目录（如 `AI/`、`Bigdata/`、`Database/` 等）的文件，应跳过 appstore 路径规范校验。如果当前该工具已存在排除列表或跳过条件，则需将根目录 `README.md` 和 `README.en.md` 等纯项目文档纳入排除范围。

### 方向 2（置信度: 低）
CI 预检工具的路径比较逻辑可能存在 bug（如相对路径 vs 绝对路径的前导 `/` 处理不一致），导致文件实际路径为 `README.md`（或 `/README.md`）通过校验后仍被误报为路径错误。需要检查 `update.py` 中路径规范化/比较的实现逻辑。

## 需要进一步确认的点
1. 查阅 `eulerpublisher/update/container/app/update.py` 第 222-273 行的 appstore 路径校验逻辑，确认其判断文件是否符合发布规范的规则（是否存在排除根目录文件的逻辑，路径比较是否严格区分前导 `/`）。
2. 确认该 CI 预检是否对**仅变更根目录文档文件**的 PR 均会触发此误报（即这是一个已知的系统性问题），还是本次 PR 特例。
3. CI 日志中 upstream 触发器显示另一 PR 编号（"PR 3184 [sunshuang1866:fix/3153 -> master]"），与本次分析上下文 PR #3153 不完全一致。建议确认 CI 日志是否确实对应 PR #3153，而非其修复 PR #3184。

## 修复验证要求
（不适用——infra-error 类型，与 PR 代码变更无关，无需 code-fixer 修改任何源文件。）
