# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: N/A
- 新模式症状关键词: N/A

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 `eulerpublisher` 对仓库根目录下的 `README.md` 执行了路径校验，报告 `[Path Error]` 并判定 FAILURE。然而该文件在仓库中的实际路径即为 `/README.md`（仓库根目录），与工具声称的"预期路径"完全一致。此失败属于 CI 工具层面对非镜像文件误触发了 appstore 发布路径校验，与 PR 的代码变更无关。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录下的两个 README 文件（`README.md` 和 `README.en.md`），内容为更新基础镜像的可用 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`，调整排序）。PR 未涉及任何 Dockerfile、`meta.yml`、`image-info.yml`、`image-list.yml` 或其他镜像构建/发布相关文件的变更。CI 失败由 `eulerpublisher` 工具的 appstore 发布预检逻辑将根级 README 变更误判为镜像发布提交而触发，与 PR 的实际内容无因果关联。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线层面的问题——`eulerpublisher` 的 appstore 发布预检模块不应对仓库根目录下的 `README.md` / `README.en.md` 变更触发路径校验。建议在 CI 工具（`update.py`）中增加逻辑：当检测到的 changed file 仅包含根级文档文件（如 `README.md`、`README.en.md`）且不涉及任何镜像目录下的文件时，跳过 appstore 发布规范预检。此方向属于 CI 基础设施侧的调整，不在本 PR 的代码修改范围内。

### 方向 2（置信度: 低）
若 CI 工具不支持方向 1 的改造，可考虑在 `update.py:356` 附近的 diff 检测逻辑中，对根级 README 文件做白名单过滤，使其不进入后续的 `line:273` 路径校验流程。同样属于 CI 工具侧变更，非 PR 代码修复。

## 需要进一步确认的点
1. **CI 工具路径比较逻辑**：`update.py` 中路径校验的具体实现——为何 `/README.md`（文件实际路径）与预期路径 `/README.md` 相同却被判定为 FAILURE。需排查是否存在路径格式不匹配（如是否因缺少前导 `/` 或绝对/相对路径不一致导致字符串比较失败）。
2. **CI 工具对根级文件的处理策略**：确认 `eulerpublisher` 在设计上是否预期对仓库根目录的非镜像文件（如项目主 README）执行 appstore 路径校验，还是此行为属于未预期到的边界情况。
3. **日志完整性**：当前日志仅来自 x86-64 job，需确认 aarch64 等下游架构 job 是否有额外的失败信息（尽管大概率会复现相同错误）。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑（如添加根级 README 白名单过滤），code-fixer 必须在提交前：
1. 从 CI 环境中获取或本地模拟 `update.py` 的 diff 检测与路径校验流程
2. 验证修改后的逻辑对纯文档 PR（仅修改根级 README）正确跳过 appstore 预检
3. 同时对包含镜像文件变更的正常 PR 仍能正确执行路径校验，确保不引入回归
