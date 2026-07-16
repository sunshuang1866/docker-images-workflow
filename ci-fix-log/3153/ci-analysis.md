# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 路径格式校验不匹配
- 新模式症状关键词: Path Error, expected path, eulerpublisher, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）在验证 `README.md` 文件路径时，期望路径格式为 `/README.md`（带前导 `/`），但 `git diff` 输出或工具解析到的路径为 `README.md`（不带前导 `/`），路径格式字符串不匹配导致校验失败。

### 与 PR 变更的关联
**直接关联。** PR #3153 修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档变更，更新可用基础镜像标签列表）。CI 检测到 `README.md` 在变更文件列表中，将其纳入 appstore 发布规范预检范围。由于 CI 工具对路径格式的前导 `/` 有严格要求，而 diff 输出路径不含前导 `/`，触发校验失败。

该 `README.md` 是仓库根级文档文件（不隶属于任何应用镜像目录），本不应被 appstore 镜像发布规范检查到，属于 CI 工具对纯文档 PR 的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `eulerpublisher` 的 `update.py` 在解析变更文件路径后、与期望路径比较前，缺少路径标准化步骤（未统一添加/移除前导 `/`）。修复应在 CI 工具侧：对 `git diff` 输出的相对路径统一添加前导 `/`，或在校验比较时规范化双方路径格式（如统一 `os.path.normpath` 处理）。若项目不便修改 CI 工具本身，可考虑为根级纯文档 PR（仅修改仓库根层的 `*.md` 文件者）在 CI 中增加豁免逻辑，跳过 appstore 发布规范预检。

### 方向 2（置信度: 低）
`README.md` 和 `README.en.md` 的内容变更（新增 `24.03-lts-sp4`、`25.09` 等标签条目以及对应的 URL）可能触发了 CI 其他未在日志中展示的校验（如链接可达性检查）。当前日志缺乏此类信息，无法确认。

## 需要进一步确认的点
1. **PR #3153 与 PR #3184 的关系**: CI 日志显示流水线由 PR #3184（分支 `fix/3153`）触发，而非 PR #3153 本身。需确认 PR #3153 原始 CI 失败的完整日志，以排除 PR #3184 的修改对失败产生了额外影响。
2. **CI 工具路径解析逻辑**: 需查阅 `eulerpublisher/update/container/app/update.py` 第 222-273 行的路径解析和比较逻辑，确认前导 `/` 的处理方式。
3. **历史同类问题**: 模式11 中 PR #2512 的 `.claude/agents/README.md` 路径校验失败与此类似但本质不同（那是子目录层级错误，这里是格式不匹配）。建议确认是否存在另一条针对根级文档的相似历史案例。
4. **aarch64 等并行 job 的状态**: 日志仅覆盖 x86-64 job，需确认 aarch64 等其他架构 job 是否也因同样原因失败。

## 修复验证要求
若修复方向 1 中涉及修改 `eulerpublisher` 工具的路径处理逻辑，code-fixer 必须：
- 从 `eulerpublisher` 对应版本源码中获取 `update.py` 的路径解析相关方法（`_parse_image_info`、路径比较逻辑等）
- 在本地用不同路径格式的 diff 输出验证标准化逻辑是否能正确处理有/无前导 `/` 的路径
- 确认修复后不会破坏其他路径校验规则（如应用镜像目录中 `{image-version}/{os-version}/Dockerfile` 的两级路径结构校验）
