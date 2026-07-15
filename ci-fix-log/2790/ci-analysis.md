# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对 PR 变更文件执行路径校验，PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（均为纯文档文件），这些文件不属于任何有效的 appstore 镜像发布制品（Dockerfile、meta.yml、image-info.yml 等），因此路径校验判定为 FAILURE。CI 的 appstore 预检流程针对所有 PR 触发，README-only 的文档类 PR 无法通过该检查。

### 与 PR 变更的关联
PR 的改动**直接触发**了该失败。该 PR 仅包含 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表的文本更新（新增 24.03-lts-sp3 / 25.09 / 24.03-lts-sp2 条目）。CI 管道将所有 PR 变更统一视为潜在的 appstore 发布请求，对变更文件进行路径和白名单校验，纯文档变更因不含必要的镜像发布元数据文件而被拒。**这是 CI 编排层面的覆盖范围问题，而非 PR 代码内容有误。**

## 修复方向

### 方向 1（置信度: 中）
该 PR 的 CI 失败属于 **CI 管道的误报**——appstore 发布规范预检不应拦截纯文档 PR（如 README 更新）。修复方向是调整 CI 编排逻辑（`eulerpublisher` 或 Jenkins pipeline），使其在检测到 PR 仅包含文档类文件（如 `README.md`、`README.en.md`、`*.md` 等无对应 image 目录结构的文件）时跳过 appstore 发布校验，直接视为通过。具体来说，可在 `update.py` 的 diff 差异检测阶段添加文件白名单过滤，排除仅含根目录非镜像文件变更的 PR。

### 方向 2（置信度: 低）
若 CI 编排逻辑不便修改，可考虑在 PR 中同时提交一个虚拟的合规文件（如在某个已有镜像目录下补一个 meta.yml 条目），以满足 appstore 校验的最低要求。但此方向属于 workaround，不推荐。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——它是否只检查变更文件列表中的每个文件是否符合 `{category}/{image}/{version}/{os-version}/...` 的镜像发布路径规范，还是会无条件将根目录 `README.md` 判定为非法路径。
2. 该 CI 管道是否有 README-only PR 的豁免机制（如 `.ci/skip-appstore-check` 标记文件或 label），如果有，PR 作者可能只需在 PR 上添加相应标签即可跳过该检查。
3. 日志中仅显示了 x86-64 的 job 日志，确认是否有其他架构的 job 日志可提供更多上下文（不过根因推断已较明确，此项为低优先级）。

## 修复验证要求
若修复方向选择调整 CI 编排逻辑（方向 1），code-fixer 必须：
- 从 `eulerpublisher` 仓库拉取对应版本的 `update/container/app/update.py`，理解 diff 检测和路径校验的完整调用链后再提交修改。
- 验证修改后的逻辑在包含 README-only 变更的 PR 上不会报错，同时确保包含真正镜像发布制品（Dockerfile + meta.yml + image-info.yml）的 PR 仍能正常通过校验。
