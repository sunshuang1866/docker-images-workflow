# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path, /README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中修改的根级 `README.md` 文件执行了路径校验，报告 `[Path Error] The expected path should be /README.md`。`README.md` 本身位于仓库根目录（路径即 `/README.md`），该检查系误报——可能是 CI 工具在对 diff 中文件路径进行归一化时，未给根级文件加上 `/` 前缀，导致 `README.md` ≠ `/README.md` 的比较失败。

### 与 PR 变更的关联
**直接相关**，但属于 CI 工具缺陷。PR 仅修改了根级 `README.md` 和 `README.en.md` 的标记列表文档内容（更新 SP2→SP3、新增 25.09 和 24.03-lts-sp2 条目），并未添加任何 Docker 镜像、`meta.yml`、`image-info.yml` 等需受 appstore 发布规范约束的文件。CI 的 appstore 预检工具不应将纯文档类 PR 纳入路径校验范围，或其对根级文件路径的归一化逻辑存在 bug。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具的路径归一化逻辑问题**：`update.py` 在获取 `git diff` 变更文件列表时，可能得到不带前导 `/` 的相对路径（如 `README.md`），而路径校验时与期望的绝对路径 `/README.md` 做全等比较，导致根级文件的路径校验始终失败。需修复 `update.py` 中路径比较逻辑，统一归一化为绝对路径格式后再比对。

### 方向 2（置信度: 低）
**CI 预检范围过宽**：`update.py` 的 appstore 规范检查未过滤掉纯文档类变更（如仅修改根级 README），对不涉及镜像发布的 PR 也执行了路径校验。可在 `update.py` 中增加前置过滤：若 diff 中所有变更文件均不在 `image-list.yml` 覆盖的镜像目录下，则跳过路径校验。

## 需要进一步确认的点
1. `update.py:273` 附近的代码逻辑，确认路径比较时是否使用绝对路径前缀。
2. `update.py:356` 处 `Difference: ["README.md"]` 的路径来源——该路径是从 `git diff --name-only` 获取的相对路径还是已归一化的绝对路径。
3. 确认该 CI 检查是否对所有仅修改根级文档的 PR 均会失败（历史复现性），还是本次 PR 特有。

## 修复验证要求
（不适用——本问题不涉及正则 patch 外部源文件。）
