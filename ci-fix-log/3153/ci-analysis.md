# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI误检根README路径
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范预检）
- 失败原因: CI 工具 `eulerpublisher` 的 appstore 发布规范预检器将仓库根目录下的 `README.md` 纳入了路径校验范围，但其路径校验规则（期望路径为 `/README.md`）与 root README 的实际路径之间产生了错误判定。该文件是仓库根级文档，不属于任何镜像目录层级，不应接受 appstore 发布规范的路径格式校验。

### 与 PR 变更的关联
- **与 PR 变更无直接因果关系**。PR 仅修改了仓库根目录下 `README.md` 和 `README.en.md` 两个文档文件中的基础镜像可用 Tags 列表（添加 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，并将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`）。
- CI 日志显示差异检测仅发现 `README.md` 变更（未检测到 `README.en.md`），随后对该文件触发了 appstore 发布规范预检，而根目录 README 本不应属于此预检的范围。
- 失败由 CI 工具的路径校验逻辑缺陷引发，与 PR 的具体文档修改内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题——`eulerpublisher` 的 appstore 预检器未正确排除仓库根目录下的 README 文件。Code Fixer 无需处理任何代码；应由 CI 维护团队在 `eulerpublisher` 工具中增加对根级 README 文件的豁免逻辑（例如在 `update.py` 的路径校验逻辑中判断文件是否处于仓库根目录，若是则跳过 appstore 路径格式检查）。

### 方向 2（置信度: 低）
若 CI 无法快速修复，可尝试将 `README.md` 和 `README.en.md` 的空提交（无实质性变更）或合并到其他有效 PR 中，绕过该 CI 预检。但由于 PR 的实质内容是对基础镜像 Tags 列表的必要更新，建议优先修复 CI 工具侧。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的具体路径校验逻辑——确认为何根级 `README.md` 会进入 appstore 发布规范检查流程、路径匹配失败的具体原因。
2. CI 差异检测（`update.py:356`）为何仅捕获到 `README.md` 而未检测到 `README.en.md`——是否存在文件过滤规则导致英文 README 被忽略。
3. 该 CI 预检是否为最近新增的检查规则——判断是否因 CI 工具更新引入了此误报。
