# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
  There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 的 appstore 发布规范预检步骤）
- 失败原因: 本 PR 仅修改了仓库根目录下的两个 README 文件（`README.md`、`README.en.md`），但 CI 的 appstore 发布规范检查工具（`update.py`）会对 PR 变更的所有文件执行路径合规校验。根目录下的 README 文件不属于任何 Docker 镜像的构建交付物（Dockerfile、entrypoint 脚本等），不在 appstore 发布规范定义的有效路径白名单中，因此被判定为路径错误。

### 与 PR 变更的关联
**直接关联**。PR 的 diff 仅包含 `README.md` 和 `README.en.md` 的文档修改（更新 Tags 列表，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）。这正是 CI appstore 路径检查所拦截的变更。PR 没有任何 Dockerfile 或镜像构建文件的改动，触发了对纯文档变更的误判拦截。

## 修复方向

### 方向 1（置信度: 中）
跳过 appstore 发布规范检查：如果 PR 仅修改根目录下的 README / 文档文件，应在 CI 中跳过 `update.py` 的路径合规校验。这需要 CI 配置或 `update.py` 工具本身支持识别"纯文档 PR"并豁免检查（参考 `update.py:356` 处的日志 `Difference: ["README.en.md", "README.md"]`，这里已识别出变更文件列表，可据此过滤）。

### 方向 2（置信度: 中）
将 README 文件纳入 appstore 路径白名单：在 CI 检查工具的路径规范中，为仓库根目录的 `README.md` 和 `README.en.md` 添加合法路径规则，使这些基础项目文档不会触发 `[Path Error]`。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中文件路径校验逻辑的具体实现——了解它如何判断一个文件路径是否合法、白名单/黑名单机制在哪里定义。
- 该 CI appstore 发布规范检查是否对**所有** PR 都会执行，还是仅在特定条件下触发（如 PR 中包含 `image-list.yml` 变更时）。
- `README.md` 的路径 `README.md` 与期望路径 `/README.md` 是否仅存在斜杠前缀差异（一个带 `/`，一个不带），这是否是 CI 工具的比较逻辑 bug 导致连合法文件也为误判。

## 修复验证要求
（无正则 patch 外部源文件的操作，无需额外验证）
