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
2026-06-30 11:28:09,089-/home/jenkins/.../update.py[line:273]-ERROR:
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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本（`update.py`）对 PR 中变更的文件进行路径合规校验。PR 修改了仓库根目录下的 `README.md` 和 `README.en.md`，但这两份文件不在 appstore 应用镜像的预期路径结构内（appstore 发布检查期望变更文件位于应用镜像的 `{image-version}/{os-version}/` 目录树下），导致路径校验失败。

### 与 PR 变更的关联
PR 仅修改了两份根级 README 文件：
- `README.md`：更新 openEuler 可用镜像 Tags 列表（移除过时的 `24.03-lts-sp2` 指向，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 独立条目）
- `README.en.md`：同上，英文版同步更新

这些变更是纯粹的文档维护，不涉及任何 Docker 镜像、代码或配置。但 CI 流水线对**所有 PR 统一执行** appstore 发布规范预检，该预检脚本将根级 README 文件变更视为"不符合 appstore 发布路径规范"而拒绝通过。

**此失败与 PR 改动的内容无直接因果关系**——即使 PR 中的文档修改完全正确，也会因预检规则与 PR 性质（纯文档 PR）不匹配而失败。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检规则需要排除纯文档 PR。当 PR 仅包含根级文件（如 `README.md`、`README.en.md`、`.github/` 下的配置等）的变更，且不涉及任何 `{category}/{image}/{version}/{os-version}/` 路径下的镜像文件时，应跳过 appstore 路径校验。需要检查 `update.py` 中 diff 文件列表过滤逻辑，增加对非镜像路径变更的豁免。

### 方向 2（置信度: 低）
或许 PR 标题/描述中指定了不正确的 target 路径，导致 CI 预检脚本误将此 PR 当作 appstore 上架 PR 处理。检查 CI 是否根据 PR 元数据（而非实际变更文件）来决定执行哪些预检步骤。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 `line:273` 附近的校验逻辑：该脚本是根据何规则判断"Path Error"的，是否只检查 diff 文件列表而不判断文件类型/用途
2. CI 流水线中 appstore 预检步骤是否有对纯文档 PR 的跳过机制（如通过 PR label、PR 标题关键词 `docs` 或变更文件路径模式匹配）
3. 该仓库是否存在只允许通过 appstore 发布路径修改 README 的规范约束（即在仓库文档中约定"不要在根级 README 提交 PR"），若有则此失败为预期行为而非 CI 误判

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。（此问题为 CI 预检逻辑问题，不涉及对第三方上游源文件的修改。）
