# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误

```
2026-06-29 15:21:37,042 - INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-29 15:21:41,552 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个文档文件，这两个文件不在 appstore 应用镜像发布规范的合法路径范围内（appstore 期望的路径为 `{场景分类}/{镜像名}/{版本}/{OS版本}/Dockerfile` 等应用镜像构建目录下的文件）。CI 预检工具检测到文件变更中不包含任何符合 appstore 规范的路径，因此拒绝了该 PR。

### 与 PR 变更的关联
PR 的改动（更新 README.md 和 README.en.md 中基础镜像的 Tags 列表）**直接触发**了该失败。CI 的 `update.py` 检测到 PR 变更了仓库根目录的文件后，对变更文件进行了 appstore 发布规范路径校验，但根目录 README 文件不在 appstore 允许的路径白名单内，导致检查失败。

## 修复方向

### 方向 1（置信度: 高）
此 PR 为纯文档更新（新增 `24.03-lts-sp3`、`25.09` 等 Tags 链接），不涉及任何应用镜像 Dockerfile 的构建。CI 的 appstore 发布规范预检要求 PR 变更的文件必须符合 appstore 合法的目录结构路径，根目录 README 文件不属于此范畴。

**这不是代码错误，而是 CI 策略冲突**——CI 的 appstore 预检流程不适合纯文档更新的 PR。需确认：
- CI 是否对该仓库有单独的文档 PR 处理策略（如跳过 appstore 预检）
- 是否需要将文档变更与应用镜像变更分开提交

### 方向 2（可选，置信度: 中）
若仓库策略要求所有 PR 必须通过 appstore 预检，则纯文档 PR 无法合入。可能需要与 CI 维护团队沟通放宽 appstore 预检的白名单范围，或为文档类 PR 设置免检通道。

## 需要进一步确认的点
1. CI `update.py` 中 appstore 发布规范预检的路径白名单具体包括哪些路径，以及对根目录 README 文件是否有特殊豁免规则
2. 该仓库历史上是否有纯 README 文档变更的 PR 成功合入的先例，若有则其 CI 配置与当前有何不同
3. `PR #2512`（历史案例中 `.claude/README.md` 路径违规）的最终处理方式，可参考其解决策略
