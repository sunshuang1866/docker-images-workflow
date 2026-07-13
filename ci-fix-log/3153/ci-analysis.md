# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11（变体）
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-...-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具对所有 PR 变更文件进行路径校验。本 PR 仅修改了仓库根目录下的文档文件 `README.md` 和 `README.en.md`，这两个文件不是任何应用镜像定义的一部分（不属于任何 Dockerfile 镜像目录），因此 appstore 校验工具无法将它们匹配到任何有效的应用镜像定义，报出 `[Path Error]`。

### 与 PR 变更的关联
PR 的改动（仅更新 README 中的基础镜像 tags 链接）间接触发了此失败——这些根目录文档文件的路径不在 CI appstore 校验工具的预期路径白名单中。失败与 PR 的具体内容（tag 链接是否有效）无关，仅与"修改了根目录 README 文件"这一事实相关。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施/工具侧的问题。CI appstore 校验工具不应拦截纯文档变更 PR。可行的处理方式：
- CI 工具侧：在 `update.py` 中增加对根目录文档文件（如 `README.md`、`README.en.md`、`*.md` 非镜像目录下的文件）的豁免逻辑，使其跳过这些不受 appstore 规范约束的文件。
- 或者：PR 作者可将 README 文档变更与镜像变更分开提交（文档变更单独走不受 appstore 校验约束的流程）。

### 方向 2（可选，置信度: 低）
如果仓库规范要求根目录 README 文件也必须有对应的 appstore 条目定义，则需要在某个 `image-list.yml` 或元数据中为根目录 README 文件注册路径。但从仓库结构来看，根目录 README 不应属于 appstore 镜像体系。

## 需要进一步确认的点
- 确认该 CI job 是否对所有修改根目录 README 的 PR 都会触发 appstore 校验并失败（历史同类案例）。
- 确认该仓库的 CI 配置中是否有针对纯文档 PR 的跳过机制（如 `.ci/skip-check` 或类似标记文件）。
- 查看 `eulerpublisher/update/container/app/update.py:273` 附近的校验逻辑，确认路径校验的具体规则和豁免条件。

## 修复验证要求
不适用。本失败不涉及代码文件修改，属于 CI 工具/流程侧问题。
