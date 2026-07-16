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
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.

+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 PR 变更了根目录下的 `README.md`，但该文件不属于任何应用镜像的最小目录单元，无法通过 appstore 路径校验规则，报 Path Error。

### 与 PR 变更的关联
PR 仅修改了两个根级 README 文件（`README.md` 和 `README.en.md`），更新了"可用镜像 Tags"列表的描述（添加 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2`，并修正 latest tag 对应的链接）。这是一个纯文档更新 PR，不含任何 Dockerfile、meta.yml、image-info.yml 等镜像构建相关文件。CI 的 appstore 发布规范检查（`update.py`）被 Pipeline 触发，但该检查工具的路径校验逻辑要求变更文件必须属于合法的应用镜像目录结构（如 `Category/ImageName/Version/OS-Version/Dockerfile`），根级 README.md 不符合该约束，因此校验失败。

## 修复方向

### 方向 1（置信度: 中）
PR 本身是纯文档修改，不涉及任何镜像构建或发布。CI 的 appstore 规范检查不应在此类 PR 上运行或被触发。建议在 CI Pipeline 触发条件中增加过滤逻辑，当 PR 仅包含非镜像目录下的文档文件（如根级 `README.md`、`README.en.md`）变更时，跳过 appstore 规范检查步骤。此方向需要修改 CI/Jenkins 流水线配置，而非 PR 代码本身。

### 方向 2（置信度: 低）
如果 appstore 检查必须对所有 PR 执行且无法跳过，则可能需要在 `update.py` 的校验逻辑中增加对根级 README 文件的白名单规则，允许根级 `README.md` / `README.en.md` 通过路径校验。

## 需要进一步确认的点
1. CI Pipeline（Jenkins）中触发 appstore 规范检查的条件是什么——是否有办法根据变更文件类型跳过该步骤。
2. `update.py:273` 附近的路径校验逻辑具体是如何实现的——是基于白名单匹配还是基于目录结构的严格层级检查（如 `{category}/{image}/{version}/{os}/Dockerfile` 模式）。获取 `update.py` 源码（特别是第 220-280 行）可进一步确认根因。
3. 该 CI 流水线是否预期的行为是所有 PR 都必须包含合法的 appstore 镜像内容；如果是，则此 PR 本身不应以当前形式提交。
