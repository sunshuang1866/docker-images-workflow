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
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
...
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本检测到 PR 仅包含根目录 `README.md`（及 `README.en.md`）的变更，将其视为不符合 appstore 镜像发布路径规范的变更，从而报 `Path Error` 并标记构建失败。该 PR 为纯文档修正（更新可用基础镜像 tag 列表），不涉及任何镜像 Dockerfile 或元数据文件的增删。

### 与 PR 变更的关联
PR 变更仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个文件，更新了可用基础镜像 tags 列表（将默认 tag 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09` 等条目）。CI 的 appstore 校验工具将根目录 README 变更视为"未遵循指定路径"的无效变更，拒绝通过。该失败**与 PR 内容直接相关**，但**并非 PR 文档内容有误**，而是 CI 校验逻辑对纯文档类 PR 的兼容性不足。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范校验脚本（`eulerpublisher/update/container/app/update.py`）对根目录 `README.md` 的路径校验规则可能存在过严或边界情况处理缺失。需确认该脚本是否支持纯文档类 PR（不涉及任何镜像目录变更），若支持则需要排查为何路径 `README.md` 会被判定为不符合预期的 `/README.md`；若不支持，则需调整 CI 校验策略，允许仅包含根级文档变更的 PR 通过 appstore 规范检查。

### 方向 2（置信度: 低）
PR 中 README.md 的变更可能被 CI 系统的触发器误识别为需要走 appstore 发布流程（例如将 README 修改错误匹配到了某类镜像发布事件），导致触发了本不应运行的 appstore 校验 job。若该 CI 流水线是由"文件变更路径匹配"触发，可检查触发规则是否正确排除了仓库根目录文档文件。

## 需要进一步确认的点
- 确认 CI appstore 校验脚本 `update.py:273` 附近对文件路径的解析逻辑，是否存在路径前缀 `"/"` 与实际 `git diff` 输出（不含前导 `/`）不匹配的问题。
- 确认该 CI 流水线是否有针对纯文档 PR 的跳过机制（如 `.md` only changes 自动豁免检查）。
- 确认 repository 根目录的 `README.md` 是否在 CI 的 appstore 发布白名单/黑名单中——该路径显然不属于任何镜像目录，理论上应被 appstore 校验跳过而非报 FAILURE。

## 修复验证要求
（不适用——修复方向不涉及对第三方/上游源文件的正则 patch。）
