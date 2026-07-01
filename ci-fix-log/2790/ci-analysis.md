# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-... update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 规范校验器扫描 PR 中变更的文件（`README.md`、`README.en.md`），判定两者均不符合 appstore 发布规范的路径要求，报出 `[Path Error]`。

### 与 PR 变更的关联
**由 PR 变更直接触发，但与变更内容本身无关。** 此 PR 仅修改了仓库根目录下的两个 README 文件（`README.md`、`README.en.md`），新增了两个版本 tag（`24.03-lts-sp3`、`25.09`）并调整了条目顺序。这是纯粹的文档更新，不涉及任何 Dockerfile 或应用镜像代码。CI 的 appstore 路径校验器按照应用镜像发布规范严格校验所有变更文件的路径，根级 README 文件未登记在任何应用镜像的期望路径清单中，因此被拒绝。

## 修复方向

### 方向 1（置信度: 高）
**CI appstore 校验器需支持根级 README 文件的路径豁免。** 当前的 `update.py:273` 校验逻辑将所有 PR 变更文件纳入 appstore 路径规范检查，而根级纯文档文件（如 `README.md`、`README.en.md`）不属于任何应用镜像条目，不应要求其符合应用镜像路径规范。若校验器无法自动区分"应用镜像文件"与"根级文档文件"，则需在 `update.py` 中增加对根级文档文件（路径不包含任何场景子目录，如 `AI/`、`Bigdata/` 等）的豁免逻辑。

### 方向 2（置信度: 中）
**路径比较格式不一致导致误判。** 注意到 `README.md` 的实际路径就是 `/README.md`，与校验器期望路径相同却仍报 FAILURE，可能是路径比较时缺少前导 `/` 导致字符串不匹配（如实际路径为 `README.md`，期望路径为 `/README.md`）。若问题仅为格式不一致，修正路径格式化逻辑即可，`README.en.md` 仍需单独的豁免处理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 222-273 行附近的具体校验逻辑（路径比较方式、期望路径来源、是否有根级文件豁免规则）。
2. `README.en.md` 是否为该仓库 appstore 规范允许的额外根级文档文件，还是应合并到 `README.md` 中（即不再维护独立的英文 README）。
3. 历史上是否有其他仅包含根级 README 变更的 PR 通过此校验（用于判断是否为近期引入的回归问题）。

## 修复验证要求
无需特殊验证。此类修复不涉及正则 patch 外部源文件，修改范围限于 CI 校验脚本 `eulerpublisher/update/container/app/update.py` 的路径过滤逻辑。

code-fixer 若修改 `update.py`，必须：
- 确认修改后，仅根级 README 变更的 PR 能通过 appstore 路径校验；
- 确认修改后，包含应用镜像文件路径错误的 PR 仍能被正确拦截。
