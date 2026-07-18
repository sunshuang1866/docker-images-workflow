# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（部分相关）
- 新模式标题: 根README路径校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455 - update.py[line:356] - INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,677 - update.py[line:222] - INFO: Clone ... successfully.
2026-07-14 15:28:07,685 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: CI 的 appstore 发布规范检查（`update.py`）检测到 PR 修改了仓库根目录的 `README.md`，路径校验规则将其判定为不符合 appstore 发布规范的预期路径，报 `[Path Error] The expected path should be /README.md`。CI 工具可能预期 appstore 相关 PR 的变更应局限在具体应用镜像子目录（如 `AI/`、`Bigdata/` 等）下，根级 README 文件不在其许可范围内。

### 与 PR 变更的关联
**直接关联**。PR #2790 仅修改了两个文件——`README.md` 和 `README.en.md`，均为仓库根目录的纯文档更新（更新支持的镜像 Tags 列表）。CI 将 `README.md` 识别为 diff 中的变更文件（`Difference: ["README.md"]`），并对其执行 appstore 发布规范路径校验，校验不通过导致构建失败。

## 修复方向

### 方向 1（置信度: 中）
此失败与代码质量无关，是 CI 管线机制问题：appstore 发布规范预检被错误的 PR 类型触发。该 PR 仅为根级 README 文档的标签列表更新，不应走 appstore 发布检查流程。若此检查逻辑在 CI 编排层（trigger job）中普遍应用于所有 merge_request 事件，则需确认 trigger job 的触发条件是否应排除仅修改根级文档的 PR。

### 方向 2（置信度: 低）
如果 CI 工具确实意图对所有 PR 执行路径校验（包括根级 README），而当前校验规则因路径格式不匹配（如缺少前导 `/`）误判，则可能需校准 `update.py` 中的路径规范化逻辑。但此方向可能性较低——日志中既输出的文件路径（`README.md`）与期望路径（`/README.md`）语义上指向同一文件，路径格式差异更可能是显示层面的问题而非实际根因。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 的完整校验逻辑：根级 `README.md` 被判定为路径错误的精确条件是什么
- 该 PR 的 CI pipeline 是由哪个 trigger job 编排的，是否所有 merge_request 事件都默认触发 appstore 发布规范检查
- `README.en.md` 同样被修改但未出现在 `Difference` 列表和失败检查结果中，说明 `update.py` 的 diff 检测逻辑或白名单过滤规则需要确认

## 修复验证要求
若修复方向涉及修改 CI 编排工具（trigger job 的 matcher/触发条件）或 `update.py` 的路径校验规则，code-fixer 必须在实际 CI 环境中对同类纯文档 PR（仅修改根级 README）重新触发构建，验证不再被 appstore 规范检查拦截。
