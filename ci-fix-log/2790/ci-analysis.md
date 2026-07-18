# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录文档CI校验误报
- 新模式症状关键词: Path Error, expected path should be, appstore specification, README.md, update.py, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检逻辑）
- 失败原因: CI appstore 发布规范检查工具（`eulerpublisher`）对仅修改根目录 README.md/README.en.md 的纯文档 PR 进行了错误判定。该工具预期 PR 至少包含新镜像提交所需的文件（如某子目录下的 Dockerfile、meta.yml、image-info.yml 等），当 diff 中只包含根目录 README.md 时，工具的路径校验逻辑将其视为"不符合预期路径"并标记为 FAILURE。PR 变更内容本身（更新可用镜像 Tags 列表）没有错误，`README.md` 也确实位于仓库根目录 `/README.md`，CI 失败为工具对纯文档 PR 的误报。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件，更新了可用镜像 Tags 列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目，修正 latest 指向）。这些变更不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等镜像构建/发布文件，不触发任何编译、测试或构建流程。CI 工具 `eulerpublisher` 的 appstore 发布规范预检逻辑将根目录 README.md 纳入校验范围，但因该 PR 不包含新镜像提交所需的配套文件而错误地将其标记为 FAILURE。此失败与 PR 代码变更质量无关，属于 CI 工具对文档类 PR 的边界处理问题。

## 修复方向

### 方向 1（置信度: 中）
CI `eulerpublisher` 的 appstore 发布规范预检逻辑需增加对"仅文档变更 PR"的豁免处理：当 PR diff 中只包含根目录 README.md/README.en.md 等纯文档文件且不涉及任何镜像构建目录时，应跳过 appstore 规范校验并直接 PASS。此修复需在 `eulerpublisher/update/container/app/update.py` 的校验入口处增加文件过滤逻辑。

### 方向 2（置信度: 低）
若该 CI 失败是偶发性或环境相关（例如 PR 原仓库 clone 路径解析异常导致 README.md 在工具工作目录中路径偏离），则可直接 re-run CI 验证是否复现。由于日志中路径和文件定位均正确，此可能性较低。

## 需要进一步确认的点
- 需确认 `eulerpublisher/update/container/app/update.py:273` 附近 appstore 规范校验的逻辑具体如何判定文件路径合法性，是否为"仅文档变更 PR"预留了豁免分支。
- 需确认该 PR 是否被正确标记为文档类 PR——日志中 `Difference: ["README.md"]` 说明只有 README.md 被识别为变更，但无法确认校验器是否将此信息用于分类决策。
- 需与 CI 工具维护者确认：根目录 README.md 是否应被纳入 appstore 发布规范校验范围。

## 修复验证要求
无需 code-fixer 修改正则或代码。此失败为 CI 工具对纯文档 PR 的误报，建议由 CI 工具维护者调整校验逻辑或由 PR 提交者联系 CI 管理员手动跳过该检查。
