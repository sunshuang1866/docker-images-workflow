# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对所有 PR 中变更的文件进行路径校验，要求变更文件必须位于应用镜像子目录（如 `Bigdata/`、`AI/` 等）下。PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，不含任何镜像相关文件（Dockerfile、meta.yml、image-info.yml），因此根级 `README.md` 被预检工具判定为路径不匹配，报 `[Path Error]` 导致构建标记为 FAILURE。

### 与 PR 变更的关联
PR #2790 仅包含纯文档变更：
- `README.md` — 更新"可用镜像的Tags"列表（添加 24.03-lts-sp3、25.09、24.03-lts-sp2 条目）
- `README.en.md` — 同步更新英文版 Supported Tags 列表

**PR 的改动本身没有引入任何代码错误或构建问题。CI 失败与 PR 的文档内容正确性无关，而是因为 CI 流水线将 appstore 镜像发布规范的路径检查错误地应用到了纯文档 PR 上。** 该 PR 本不应触发 appstore 发布预检流水线。

另外值得注意的是，PR diff 中 `24.03-lts-sp3` 条目出现了两次（一次在首行带 `24.03, latest` 别名，一次在第 4 行单独列出），但这是内容重复问题，与 CI 失败无直接关联。

## 修复方向

### 方向 1（置信度: 高）
**关闭此 PR 或等待 CI 流水线侧修复后再重试。** 该 CI 失败与 PR 的文档更改无关，属于 CI 流水线配置/工具问题——appstore 发布规范预检不应该对纯文档变更的 PR 执行路径校验。如果该文档变更必须合入，可能需要在 CI 触发条件中增加豁免逻辑（例如仅包含 `README*` 文件变更的 PR 跳过 appstore 检查），但这属于 CI 流水线运维侧的操作，非 PR 提交者可控。

### 方向 2（置信度: 中）
检查是否有办法绕过 appstore 检查。PR 中的文档变更本身没有问题，但在当前 CI 配置下无法通过路径校验。如果存在 CI 配置可以让文档类 PR 跳过此检查（如 PR label、特定分支命名），可尝试使用。

## 需要进一步确认的点
- 该 CI 流水线是否对所有仓库 PR 均强制执行 appstore 路径预检，还是仅针对特定触发条件
- 此前是否有类似纯文档 PR 成功通过 CI 的先例（可确认是否为本次流水线的回归问题）
- `update.py:273` 中路径校验的具体逻辑——它是如何从 PR diff 中提取文件路径并比对的
