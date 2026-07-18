# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（CI appstore 发布规范预检——路径校验失败）

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171- INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051- ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检步骤）
- 失败原因: CI 的 appstore 发布规范校验工具检测到 PR 变更了根目录下的 `README.md`，但其内部路径校验逻辑认为该文件的期望路径为 `/README.md`，与 diff 中报告的路径 `README.md`（无前置 `/`）不匹配，导致路径校验失败。该 PR 为纯文档变更（仅更新 README 中基础镜像可用 tag 列表），不涉及任何应用镜像 Dockerfile 或 meta.yml 等 appstore 发布制品。

### 与 PR 变更的关联
PR 变更仅涉及两个文件：
1. `README.md` — 更新基础镜像 tag 列表（sp2→sp4，新增 sp3、25.09、sp2 等条目）
2. `README.en.md` — 同上（英文版同步更新）

PR 未修改任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等 appstore 发布相关文件。CI 失败源于其预检工具 `eulerpublisher/update/container/app/update.py` 对 diff 中检测到的 `README.md` 执行了不恰当的 appstore 路径校验。该工具的路径字符串比较方式（diff 报告 `README.md` 无前置 `/`，而校验规则期望 `/README.md`）触发了误判。

**本次失败与 PR 代码变更无直接因果关系**——PR 的文档内容本身正确，失败是 CI 工具的路径校验机制对纯文档 PR 的兼容性问题。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑可能存在缺陷：它从 diff 中提取变更文件路径时未统一添加前置 `/`，导致与期望路径 `/README.md` 的字符串比较失败。根本修复应在 CI 工具侧（`eulerpublisher` 仓库）对 diff 提取的路径做归一化处理（统一添加或移除前置 `/`），而非在本 PR 中修改。本 PR 作为纯文档 PR，可通过 CI 侧加白名单或跳过根目录 README 文件的 appstore 校验来绕过。

### 方向 2（置信度: 低）
如果 CI 策略要求任何 PR 都必须包含至少一个有效的 appstore 发布制品（应用镜像 Dockerfile + meta.yml），则本次文档变更 PR 需要额外包含某个应用镜像的更新才能通过 CI。但这与 PR 标题 `docs:` 的意图矛盾，且不合理的 CI 策略应被修正，不建议走此方向。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 处路径校验逻辑的具体实现——确认是否因字符串前缀不一致（`README.md` vs `/README.md`）导致误判
2. CI 编排层是否对纯文档 PR（仅修改根目录 README 类文件）有白名单豁免机制，若有则需确认为何未被触发
3. 日志中 `Difference: ["README.md"]` 仅列出了 `README.md`，未列出 `README.en.md`——需确认 CI 工具的 diff 提取范围（是否仅监视特定文件名模式）
