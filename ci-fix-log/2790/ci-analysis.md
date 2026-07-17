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
2026-07-14 15:28:07,685-/home/jenkins/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具将仓库根目录的 `README.md` 纳入了路径规范校验，可能因相对路径（`README.md`）与绝对路径（`/README.md`）的字符串比较不匹配而误报 FAILURE。该 PR 仅修改了仓库根级文档文件（`README.md` 和 `README.en.md` 的 Tags 列表更新），不涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件。

### 与 PR 变更的关联
PR 变更仅涉及仓库根级 README 文件的 Tags 条目更新（4 行新增、1 行删除），属于纯文档修改。CI 工具将根级 `README.md` 纳入 appstore 发布规范校验范围属于工具行为不当——仓库根级 README 不应受 app 级路径规范约束。该失败与 PR 代码内容无关，属于 CI 工具对变更文件作用域判断的问题。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的 appstore 发布规范预检需在文件变更扫描阶段过滤掉非应用镜像目录下的文件（如根级 `/README.md`、`/README.en.md`），避免将仓库级文档误当成 app 级元数据文件进行路径校验。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 处路径校验逻辑的具体实现细节——确认是相对/绝对路径比较不一致，还是 CI 工具对文件类型识别有缺陷
- CI 日志中上游触发信息显示 `PR 3194` 与上下文 PR 编号 `#2790` 不一致，需确认 CI 日志是否对应正确的 PR（可能 3194 为 CI 系统内部编号）
- 根级 `README.md` 被纳入 appstore 检查范围的具体原因（需查看 CI 管线的文件过滤逻辑实现）
