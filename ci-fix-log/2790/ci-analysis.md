# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685- update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检将仓库根目录的 `README.md` 修改视为应校验的应用镜像文件，但其路径（仓库根级）不符合 appstore 镜像发布规范的路径要求，被判定为路径错误（`[Path Error] The expected path should be /README.md`）。

### 与 PR 变更的关联
PR #2790 仅修改了两个仓库根级文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tags 列表：
- 将 `24.03-lts-sp2` 的链接从错误的 SP1 URL 修正为 SP3 URL
- 新增 `25.09` tag 条目
- 补充 `24.03-lts-sp3` 和 `24.03-lts-sp2` 的独立条目

所有变更均为纯文档更新，**不涉及任何应用镜像 Dockerfile 的添加或修改**。CI pre-check 对根级 README 文件执行应用镜像路径校验属于 CI 工具的误报，与 PR 变更内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的预检逻辑缺少对仓库根级文档文件（非应用镜像相关）的过滤。该路径校验（第 273 行附近）应跳过不属于 `image-list.yml` 中声明的镜像目录路径的文件变更。若无法修改 CI 工具，应考虑在 PR 的变更范围判断中排除纯文档类文件。

## 需要进一步确认的点
1. CI 工具 `update.py` 中第 273 行 `Path Error` 的判断逻辑具体如何比对路径——是比对绝对路径前缀还是检查文件是否在 `image-list.yml` 注册的镜像目录下？
2. 该 appstore 预检是否对**所有** PR 强制执行，还是仅对特定目录变更触发——若对所有 PR 都执行，则需在 CI 工具侧增加白名单过滤规则。
3. 日志中差异检测（`update.py:356`）仅报告了 `README.md`，未报告 `README.en.md`，这是否说明 CI 只对 `README.md` 做了 appstore 校验——如果是，该过滤可能不完整。
