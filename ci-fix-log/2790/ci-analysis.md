# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验失败
- 新模式症状关键词: Path Error, expected path should be, /README.md, eulerpublisher, appstore

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（`update.py` 的 appstore 规范校验阶段）
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新镜像 Tag 列表），CI 的 `eulerpublisher` appstore 规范校验工具检测到 `README.md` 变更后，试图将其归类到某个 appstore 镜像的目录层级下进行路径校验，但根级 `/README.md` 不匹配任何镜像的期望路径结构（通常为 `{category}/{image}/{version}/{os-version}/...`），导致路径校验报错并标记 CI 失败。

### 与 PR 变更的关联
**与 PR 变更直接相关**。PR 仅做了纯文档变更：在 `README.md` 和 `README.en.md` 中更新镜像 Tag 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等 tag 条目，修正 `latest` 标签指向的 URL）。这些变更是合法的仓库根级文档维护，不涉及任何镜像的 Dockerfile、meta.yml 或 image-info.yml 新增/修改。CI 的 appstore 路径校验器对根级 README 变更无豁免逻辑，因此误报为错误。

## 修复方向

### 方向 1（置信度: 中）
根级 `README.md` 属于仓库整体文档，不属于任何单一 appstore 镜像。CI 的 `eulerpublisher/update.py` 在检测到 diff 变更时，应对根级 `/README.md` 做豁免处理（跳过 appstore 路径规范校验），因为根 README 是仓库门面文档，其 Tag 列表维护不遵循应用镜像的 `{image}/{version}/{os-version}/` 层级规范。修复点在于 CI 工具本身的变更过滤逻辑，而非 PR 内容。

### 方向 2（置信度: 低）
若 CI 工具不便于修改，可考虑在 PR 中将根 README 的 Tag 更新与 appstore 相关变更拆分为两个独立 PR——文档 PR 不触发 appstore 校验流水线。但这需要 CI pipeline 本身支持按变更文件类型跳过特定 job，属于 CI 配置层面的改动。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 diff 变更过滤逻辑的具体实现——确认根级 `/README.md` 是否在豁免名单中，或者豁免逻辑是否存在 bug。
2. CI 流水线配置：appstore 规范校验 job 是否有条件判断（如"仅当变更涉及 `meta.yml` / `image-info.yml` / `Dockerfile` 时才执行"），还是对所有 PR 无差别执行。
3. 同类纯文档 PR（仅修改根 README）的历史 CI 运行结果——确定这是偶发性问题还是已有先例。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher/update/container/app/update.py` 的路径过滤逻辑，code-fixer 必须在修改后，模拟构造一个仅变更根级 README.md 的 PR diff，运行 update.py 的校验流程，确认根 README 被正确跳过且不报错。
