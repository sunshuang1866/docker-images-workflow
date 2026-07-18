# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR触发路径校验
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, specification errors

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-[...]/update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-[...]/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对所有 PR 中变更的文件进行路径校验。本 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新，非 Docker 镜像提交），该文件不属于任何 Docker 镜像规范目录结构，CI 工具无法将其映射到合法的 appstore 发布路径，从而报告 `[Path Error] The expected path should be /README.md` 并判定失败。

### 与 PR 变更的关联
**与 PR 变更内容无关。** PR 的改动仅为 `README.md` 和 `README.en.md` 中镜像 tag 列表的文档更新（将 latest 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，并补充 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 独立条目），代码变更本身没有错误。失败根因是 CI 流水线对纯文档类 PR 也执行了 appstore 发布规范检查，而该检查预期变更文件应属于某个 Docker 镜像的最小目录单元（如 `{category}/{image}/{version}/{os-version}/...`），根级 `README.md` 不符合此预期，导致检查失败。

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施层面的误报，与代码无关。无需修改 PR 中的任何文件。应检查 CI 流水线配置或 `eulerpublisher/update.py` 中的检查逻辑，使其在 PR 仅包含根级文档文件变更时跳过 appstore 发布规范预检，或将根级 `README.md` / `README.en.md` 加入豁免白名单。

### 方向 2（置信度: 低）
如果 CI 流水线期望所有 PR（包括纯文档 PR）都必须通过 appstore 检查，则需将根级 `README.md` 和 `README.en.md` 纳入某个 `image-list.yml` 的条目中，或调整检查规则使其接受根级文档路径。但从项目结构来看，根级 README 是仓库级文档而非应用镜像文档，这种做法不符合项目规范。

## 需要进一步确认的点
1. CI 流水线配置（Jenkinsfile 或触发规则）中，appstore 检查是否有针对纯文档 PR 的跳过逻辑，若有则需排查为何本次未生效。
2. `eulerpublisher/update/container/app/update.py` 中 `line:273` 附近的路径校验逻辑，确认是否有文件类型或路径前缀的白名单/黑名单机制。
3. `README.en.md` 同时也被修改但未出现在错误报告中——需确认是该文件未被扫描，还是仅报告第一个失败文件后即终止。

## 修复验证要求
无需验证（infra-error，非代码修复范畴）。
