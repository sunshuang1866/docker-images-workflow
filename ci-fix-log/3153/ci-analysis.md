# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文档被误检
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范检查工具（eulerpublisher）扫描到 PR 对根级 `README.md` 有变更后，将其纳入 appstore 镜像路径校验流程。工具要求文件路径必须以 `/` 开头（即期望 `/README.md`），而 diff 输出的相对路径 `README.md` 不满足该格式约束，导致校验失败。

### 与 PR 变更的关联
PR #3153 仅修改了两个根级文档文件（`README.md` 和 `README.en.md`），用于更新基础镜像可用 Tags 列表，**不涉及任何应用镜像 Dockerfile、meta.yml、image-list.yml 或 image-info.yml 的变更**。CI 工具 eulerpublisher 的 appstore 发布规范检查将所有变更文件（含根级纯文档文件）无差别纳入镜像路径校验，导致误报。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，与 PR 代码变更无关。eulerpublisher 工具应过滤掉根级纯文档文件（如 `README.md`、`README.en.md`），仅对 `Bigdata/`、`AI/`、`Cloud/` 等应用镜像目录下的文件执行 appstore 路径校验。该修复需由 CI 团队在 eulerpublisher 工具侧进行，而非 PR 作者。

### 方向 2（置信度: 低）
如果 CI 工具对根级文件校验是预期行为（要求路径以 `/` 前缀输出），则可能是上游 CI 脚本中 `git diff` 路径格式提取逻辑的 bug——应输出绝对路径 `/README.md` 而非相对路径 `README.md`。同样属于 CI 基础设施范畴，PR 作者无需处理。

## 需要进一步确认的点
1. eulerpublisher 工具的 appstore 发布规范检查是否有白名单机制来排除根级文档文件？查看 `update.py` 中第 222-273 行附近的文件过滤逻辑。
2. 该 CI 检查是否在所有 PR（含纯文档 PR）中均强制执行，还是仅在该工作流中触发？如果是后者，可能需要在 trigger 层增加 diff 内容类型判断，跳过无可构建内容变更的 PR。
3. PR #3184（日志中显示 `PR 3184 [sunshuang1866:fix/3153 -> master] trigger by merge_request`）的上下文——本 PR 是否由一个修复分支触发，而该修复分支引入了其他触发条件。

## 修复验证要求
不适用——该失败为 CI 基础设施问题，无需对仓库文件做任何修改。若 CI 团队修复了 eulerpublisher 或 trigger 层逻辑，需重新触发此 PR 的 CI 以确认通过。
