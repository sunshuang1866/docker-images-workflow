# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211 - INFO: Difference: [
    "README.en.md",
    "README.md"
]
...
2026-07-12 15:33:13,075 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）检测到 PR 变更了仓库根目录的 `README.md` 和 `README.en.md` 两个文件，但该检查期望变更文件符合应用镜像的路径规范（如 `{category}/{image-version}/{os-version}/README.md`），根目录下的文档文件不匹配该期望路径，导致 `[Path Error]` 校验失败。

### 与 PR 变更的关联
PR 仅修改了根目录的两个 README 文件（更新基础镜像可用 Tags 列表），属于纯文档变更，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml。CI 的 appstore 路径校验机制对所有 PR 变更文件执行统一检查，但未对纯文档类 PR 做豁免处理，导致本应通过的文档更新被误判为路径违规。此失败与 PR 的文档修改内容无关，属于 CI 校验逻辑未适配文档类 PR 的场景。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 路径校验检查应排除仓库根目录的非应用镜像文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等顶层文档）。可在 `update.py` 的 diff 文件列表中过滤掉根目录文档文件，使纯文档类 PR 不受 appstore 路径规范约束。

### 方向 2（置信度: 中）
如果是 CI 配置问题（如该 PR 不应触发 appstore 检查 workflow），可通过调整 Jenkins pipeline 的触发条件，使仅变更根目录文档的 PR 跳过 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验步骤。

## 需要进一步确认的点
- 确认 CI 的 appstore 路径检查是否有白名单机制，以及根目录 README 文件是否应被纳入白名单。
- 确认 `update.py` 中路径校验逻辑（第 273 行附近）是否已有对根目录文件的过滤逻辑，以及为何对 `README.md` 和 `README.en.md` 报 "expected path should be /README.md" 的路径错误。
- 确认该 CI workflow 是否有架构专属下游 job 的输出日志需要查看（当前日志为主 job，可能还有 x86-64/aarch64 下游 job 的日志需交叉验证）。
