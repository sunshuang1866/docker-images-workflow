# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验异常
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具对仓库根目录的 `README.md` 执行路径校验时，从 git diff 获取的文件路径为 `README.md`（不带前导 `/`），而工具内部期望路径为 `/README.md`（带前导 `/`），路径字符串比对因缺少前导斜杠规范化而失败。该文件确实位于仓库根目录，路径本身没有问题，错误源于 CI 工具侧的路径比对逻辑缺陷。

### 与 PR 变更的关联

PR 仅修改了仓库根目录的两个文档文件（`README.md` 和 `README.en.md`），更新了"可用镜像的 Tags"列表：将 `latest` 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，并新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 的独立条目及对应 URL。这些变更是纯文档维护工作，不涉及任何 Dockerfile、meta.yml 或应用镜像的添加/修改，与 CI 失败无因果关联——CI 工具在校验 `README.md` 的**路径格式**时出错，而非校验其**内容**。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑存在前导 `/` 规范化缺陷。CI 工具在对变更文件进行 appstore 路径规范检查时，应统一对 git diff 输出的相对路径和内部期望的绝对路径做前导 `/` 规范化后再比对。此修复应在 CI 工具仓库中执行，PR 作者无需对本次提交的 README 文件做任何修改。

### 方向 2（置信度: 低）
若 CI 工具的行为是"设计如此"——即要求根目录 README.md 不被单独变更（必须伴随有效的应用镜像文件变更一同提交），则 PR 需补充一个有效的 Dockerfile 或 meta.yml 条目变更才能通过预检。但从错误消息"expected path should be /README.md"的语义判断，工具在校验阶段即失败（路径比对不通过）而非在业务规则阶段被拒，故此可能性较低。

## 需要进一步确认的点
1. CI 工具 `update.py` 路径校验段的源码，确认是否为前导 `/` 的字符串比对缺陷，或是否存在工作目录拼接导致的路径不一致。
2. 根目录 README.md 是否被设计为纳入 appstore 预检范围——若根 README 不应被检查，应在工具的变更文件过滤逻辑中将其排除。
3. 是否有仅修改根目录 README.md 的历史 PR 曾成功通过 CI，以判定是否为近期 CI 工具升级/配置变更引入的回归。
