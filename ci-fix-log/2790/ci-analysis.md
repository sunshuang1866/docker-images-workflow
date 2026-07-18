# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无，已匹配已有模式)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 变更了 `README.md`，将其视为 appstore 上架镜像的一部分进行路径校验。但该文件是仓库根目录下的主文档 README，并非某个应用镜像目录内的 `README.md`，不符合 CI 工具对 appstore 发布物路径的预期，导致校验失败。

### 与 PR 变更的关联
该 PR 为纯文档变更（更新 `README.md` 和 `README.en.md` 中的镜像 Tags 列表），未涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的修改。CI 的 appstore 发布规范校验工具仅根据"PR 变更了 README.md"就触发了路径校验，并将根目录 README 误判为不符合 appstore 上架规范的产物。

与历史案例 PR #2512（`.claude/README.md` / `.claude/agents/README.md` 路径不符合 appstore 规范）属于同一类 CI 校验误触及问题。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 发布规范预检工具应区分"仓库根目录 README 变更"与"应用镜像目录内 README 变更"。根目录 README 是整个仓库的说明文档，不属于任何 appstore 上架镜像，不应对其执行 appstore 路径校验。可对 CI 校验工具（`update.py`）增加过滤逻辑，排除根目录或 `Base/openeuler/` 等非应用镜像路径下的 README 文件。

### 方向 2（置信度: 中）
若方向 1 不可行（CI 工具为共享组件不便修改），可考虑将此 PR 合并到主分支时不触发 appstore 检查。但此为绕过而非修复，不推荐。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行附近 appstore 路径校验逻辑的具体实现，确认其对根目录 README 的处理方式
- CI 流水线的触发条件配置：是否可以对仅含文档变更（无 Dockerfile/meta.yml 变更）的 PR 跳过 appstore 发布校验步骤

## 修复验证要求
（无。本次失败为 CI infra 层面的校验逻辑误触及，不涉及正则 patch、外部源文件或上游代码修改。）
