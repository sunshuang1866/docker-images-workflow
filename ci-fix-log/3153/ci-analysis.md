# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（文档更新），但 CI 的 appstore 发布规范预检工具对所有 PR 变更文件进行路径格式校验。`README.md` 位于仓库根目录 `/README.md`，不属于任何应用镜像的目录结构（`Category/Image/Version/OS/...`），无法通过 appstore 镜像发布路径规范检查，导致校验失败。

### 与 PR 变更的关联
- **直接关联**：PR 变更了 `README.md` 和 `README.en.md`，触发了 CI appstore 预检工具对 `README.md` 的路径校验。
- **本质原因**：该 PR 是纯文档更新（在 README 中补充新的基础镜像 tags），不涉及任何应用镜像的 Dockerfile 或元数据变更。CI appstore 预检工具对根目录文档文件强制执行镜像路径规范校验，产生误报。

## 修复方向

### 方向 1（置信度: 高）
这是一个纯文档 PR，不应触发 appstore 发布规范预检。需要调整 CI 流水线触发器逻辑，使得仅修改根目录文档文件（`README.md`、`README.en.md` 等）的 PR **跳过** appstore 路径规范校验步骤。参考模式11 中类似案例（PR #2512 的 `.claude/README.md` 路径校验误报），CI 工具 `eulerpublisher` 的预检逻辑可能需要增加对根目录文档文件的白名单过滤。

### 方向 2（置信度: 低）
如果 CI 流水线配置无法按文件类型跳过预检，则需要将文档更新 PR 与镜像变更 PR 分离提交，确保 appstore 预检仅在包含实际镜像变更的 PR 中运行。

## 需要进一步确认的点
- CI 流水线（Jenkins pipeline）的触发条件配置，确认是否可以按变更文件类型跳过 appstore 预检阶段。
- `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现，确认是否已有白名单机制及如何扩展。

## 修复验证要求
（无 — 该 PR 不涉及正则 patch 外部源文件）
