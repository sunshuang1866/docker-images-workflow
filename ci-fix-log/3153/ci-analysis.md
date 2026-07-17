# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 路径比较未归一化
- 新模式症状关键词: Path Error, expected path should be, appstore, update.py, README.md

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`:273
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）在路径比较时，期望路径为 `/README.md`（带前导斜杠），而实际扫描到的文件路径为 `README.md`（不带前导斜杠），两者字符串不匹配，导致页面根目录的 README.md 被标记为 `[Path Error]`。这与 PR 的文档内容变更无关，属于 CI 工具路径归一化处理的缺陷。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，更新基础镜像 tags 列表（新增 SP4/SP3/25.09/SP2 条目，修正 SP2 链接）。该变更被 CI 的 `update.py`（line 356）检测到后进入 appstore 发布规范检查流程，检查在路径比对阶段因前导斜杠不一致而误报失败。**失败与 PR 变更内容本身无关，是 CI 工具对根目录文件路径处理不当导致的。**

## 修复方向

### 方向 1（置信度: 高）
在 `eulerpublisher/update/container/app/update.py` 中修复路径比较逻辑：对参与比对的路径字符串统一添加前导斜杠归一化后再比较（或在生成 expected path 时去除前导斜杠），使 `/README.md` 与 `README.md` 能正确匹配。此修复属于 CI 工具层面的改动，不涉及 docker-images 仓库的 Dockerfile 或文档内容。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中路径构造和比较的具体逻辑（line 273 附近的代码），确认为前导斜杠归一化缺失导致的误报。
- 确认 `README.en.md` 为何未出现在差异列表中（日志仅显示 `Difference: ["README.md"]`），虽然 PR diff 明确修改了两个文件。
