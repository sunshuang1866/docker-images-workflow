# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验失败
- 新模式症状关键词: Path Error, expected path, appstore, README.md, specification errors

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: 仓库根目录 `README.md`（被 CI 工具 `eulerpublisher/update/container/app/update.py:273` 拦截）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 变更了根级 `README.md`，该文件不位于任何镜像分类目录（如 `AI/`、`Bigdata/` 等）下，不符合 appstore 镜像发布路径规范（要求变更文件位于 `{category}/{image}/{version}/{os-version}/` 或 `{category}/image-list.yml` 等规范路径内），被判定为路径错误。

### 与 PR 变更的关联
PR 的改动仅涉及两个根级文档文件：
- `README.md`（中文版）— 新增 tags 25.09、24.03-lts-sp3、24.03-lts-sp2 的链接
- `README.en.md`（英文版）— 同上

这些变更是纯文档更新，不涉及任何 Dockerfile、meta.yml、image-list.yml 或镜像构建逻辑。CI 工具在 diff 检测（`update.py:356`）中识别出 `README.md` 发生了变更，随后在发布规范校验（`update.py:273`）阶段因根级文件路径不符合 appstore 镜像发布目录层级而报错。该校验逻辑似乎未对纯文档 PR 做豁免处理。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具对根级 `README.md` 这类纯文档文件的变更缺乏豁免机制。若 PR 的意图仅仅是更新文档（如刷新 tags 列表），且不涉及任何镜像发布，可考虑通过 CI 配置为根级文档文件添加白名单/豁免规则，使其跳过 appstore 发布路径校验。

### 方向 2（置信度: 低）
可能是 fork 分支（`sunshuang1866:fix/2790`）的 Cherry-pick 或 rebase 导致 `README.md` 的 diff 基础与预期不一致，CI 工具误将其当作镜像发布相关 PR 进行校验。可尝试从主仓库 master 分支同步后重新推入 PR 触发 CI。

## 需要进一步确认的点
1. 确认 CI 工具 `eulerpublisher/update/container/app/update.py` 中 `_check_readme_path` 或类似校验方法的具体逻辑，明确它对根级文件的行为是预期内的硬性拒绝还是配置问题。
2. 确认该仓库的 CI 流水线是否允许仅包含文档变更的 PR 合入 — 如果允许，则需要在 CI 校验层面对根级 README.md 等文档文件添加路径校验豁免。
3. 确认历史是否有类似根级 README 更新合入的案例，以判断这是偶发问题还是已知策略限制。
