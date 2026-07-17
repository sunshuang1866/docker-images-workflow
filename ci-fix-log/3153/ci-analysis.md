# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式（与模式11 部分相关）
- 新模式标题: 根文档触发应用商店路径校验
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

日志中检测到的差异文件仅包含 `README.md`：
```
2026-07-16 20:34:19,171-update.py[line:356]-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具的应用商店发布规范检查步骤）
- 失败原因: CI 的应用商店发布规范检查工具（`update.py`）对 PR 变更文件进行路径合规校验时，检测到仓库根目录的 `README.md` 被修改。`README.md` 是项目级别的文档文件，不属于任何应用商店镜像目录结构，但 CI 工具将其纳入了应用商店发布规范校验流程，导致产生 `[Path Error]` 并判定为 FAILURE。错误信息 "The expected path should be /README.md" 存在歧义——文件实际即位于 `/README.md`，但仍被判定为路径错误，说明 CI 工具对根目录非应用商店文件的分类处理存在缺陷。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新可用基础镜像的 tags 列表），属于纯文档变更，不涉及任何 Dockerfile、meta.yml 或应用镜像文件。CI 的应用商店发布规范检查对这类纯文档 PR 不应产生阻断性错误。当前失败是由于 CI 工具对变更文件的路径校验逻辑未能将根目录项目文档与真正的应用商店条目区分开来，属于 CI 工具对文档类 PR 的误报。

此外，需注意 CI 日志触发来源为 **PR #3184**（分支 `fix/3153`），非直接来自 PR #3153。PR #3184 可能是为修复 PR #3153 的 CI 失败而创建的，但日志中显示了相同的 Path Error，说明该问题在 fix 分支中仍未解决。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 中的应用商店路径校验逻辑需要增加对仓库根目录项目文档（如 `README.md`、`README.en.md` 等）的白名单过滤，使这些非应用商店条目不被纳入路径格式校验。具体而言，需要在差异文件检测后、路径校验前，过滤掉位于仓库根目录的非镜像文件。

### 方向 2（置信度: 低）
如果 `[Path Error]` 并非由根目录文件误检引起，而是 CI 工具在对 README.md 做内容格式或元数据校验时产生的误报，则需要检查 `update.py` 中对 README.md 的具体校验规则，确认是否存在过于严格的格式要求导致文档更新被拦截。

## 需要进一步确认的点
1. CI 工具 `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑具体是如何实现的——是在什么条件下产出 `[Path Error] The expected path should be /README.md` 这个错误信息
2. 该 CI 检查步骤对 PR 中仅修改根目录文档文件（无镜像变更）的场景，预期行为是什么——是放行还是阻断
3. PR #3184（`fix/3153` 分支）的完整 diff 内容——是否有除 README.md 之外的其他变更引入或尚未消除该问题
