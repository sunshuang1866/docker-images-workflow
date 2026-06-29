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
2026-06-29 15:21:41,552-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `/home/jenkins/agent-working-dir/workspace/multiarch/openeuler/x86-64/openeuler-docker-images/eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 检测到 PR 变更文件仅包含根目录下的 `README.md` 和 `README.en.md`，这些文件不符合 appstore 镜像发布所需的目录结构规范（期望在 `{Category}/{ImageName}/{Version}/{OSVersion}/` 路径下有 Dockerfile 等镜像构建文件），因此判定为路径错误。

### 与 PR 变更的关联
PR #2790 的变更仅为对根目录 `README.md` 和 `README.en.md` 中「可用镜像 Tags」列表的文档更新（将 latest 标签从 24.03-lts-sp2 更新为 24.03-lts-sp3，并新增 25.09、24.03-lts-sp3、24.03-lts-sp2 的独立条目）。这些变更是纯文档性质，不涉及任何 Dockerfile 或镜像构建文件。CI 的 appstore 发布规范预检步骤对所有 PR 统一执行，但对于纯文档类 PR 缺乏跳过逻辑，导致无镜像发布内容可检查而报错。

## 修复方向

### 方向 1（置信度: 低）
该 CI 失败属于 **false positive**——纯文档类 PR 不应触发 appstore 发布规范预检。如果 CI 流水线允许跳过该检查，可在 PR 中通过标签或条件跳过 appstore 校验步骤。

### 方向 2（置信度: 低）
如果 CI 流水线不支持跳过检查，则此 PR 需要在 CI 侧被手动 bypass（例如由 CI 管理员在 Jenkins 中批准忽略该错误）。文档类 PR 的 CI 失败是已知的流水线局限性。

## 需要进一步确认的点
- 当前 CI 流水线是否支持通过 PR 标签（如 `skip-ci`、`docs-only`）或路径过滤（仅 `README.md` 变更时跳过 appstore 检查）来绕行该预检步骤。
- `update.py:273` 的路径校验逻辑具体如何判断「期望路径」——日志中 `README.md` 自身也在 `/README.md` 路径下却仍报告 Path Error，需查看源码中的路径匹配规则以确认是否为校验逻辑的 bug。
- 根目录 `README.en.md` 是否被 CI 的 appstore 发布规范认可为合法的仓库文件。若不被认可，文档类 PR 修改此文件就会永久失败。

## 修复验证要求
（不适用——此为 infra-error，非代码修复问题，无需 code-fixer 进行代码修改。）
