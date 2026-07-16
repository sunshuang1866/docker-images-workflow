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
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 规范预检脚本）
- 失败原因: CI 的 appstore 发布规范预检工具将根目录下的 `README.md` 文件纳入了应用镜像路径校验流程，校验工具在路径格式匹配上产生误报（文件本身位于 `/README.md`，但校验输出路径为 `README.md` 不含前缀 `/`，导致路径校验失败）。此失败与 PR 实际代码变更无关，是 CI 工具对纯文档类 PR 错误触发了面向应用镜像发布场景的路径校验规则。

### 与 PR 变更的关联
- PR #2790 仅修改了两个根级文档文件：`README.md` 和 `README.en.md`，均为文档内容更新（更新镜像 tag 列表、添加 25.09/24.03-lts-sp3/24.03-lts-sp2 条目）。
- 日志中 CI 检测到的差异文件仅有 `README.md`。
- PR 的变更内容本身没有任何导致构建失败的问题。失败源于 CI appstore 规范预检工具（`update.py`）对根级文档文件错误执行了面向应用镜像目录的路径校验规则。
- **结论：与 PR 变更无关，属于 CI 基础设施误判。**

## 修复方向

### 方向 1（置信度: 中）
CI appstore 规范预检工具（`update.py` 的路径校验逻辑）应排除纯文档类 PR（仅修改根级 README、docs 等文件、不涉及任何应用镜像目录的 PR）。当前工具将所有 PR 中变更的文件都纳入 appstore 路径校验，导致根级 `README.md` 被误判。可在 CI 预检阶段增加前置过滤：若变更文件列表中不包含任何 `{Category}/{Image}/` 路径下的文件，则跳过 appstore 路径校验。

### 方向 2（置信度: 低）
CI 预检工具内部路径解析存在前后缀 `/` 不一致的 bug —— 实际路径 `/README.md` 在输出时被格式化为 `README.md`（去掉了前导 `/`），导致校验规则匹配失败。若确认是该问题，可在 `update.py` 中统一路径格式。

## 需要进一步确认的点
1. CI 预检工具是否预期对不包含任何应用镜像变更的纯文档 PR 执行 appstore 路径校验？如果预期跳过，则需检查为何本 PR 触发了该检查流程。
2. `update.py:273` 附近的具体校验逻辑需要查看源码，确认路径比对方式（绝对路径 vs 相对路径），判断是否存在路径格式化 bug。
3. 日志中 CI 检测到的差异文件仅包含 `README.md`，未出现 `README.en.md`——需确认 `README.en.md` 被忽略的原因（是工具仅检测特定文件类型还是存在其他过滤逻辑），排除可能的路径遗漏风险。
