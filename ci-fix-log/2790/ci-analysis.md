# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用，已匹配模式11)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检步骤）
- 失败原因: 本 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像 Tags 列表），属于纯文档变更。但 CI 的 appstore 发布规范检查将所有被修改的文件均视为应用镜像候选文件进行路径校验，根级 `README.md` 不在 appstore 期望的 `{image-version}/{os-version}/` 路径结构中，因此被判定为路径不合规。

### 与 PR 变更的关联
PR 变更仅涉及两处文档修改：
- `README.md`（根目录）：更新了 `24.03-lts-sp2 → 24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 等 Tags 链接
- `README.en.md`（根目录）：同上同步更新

这些变更**不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 或 image-list.yml**，纯属仓库顶层文档维护。CI 的 appstore 预检工具未能区分根级文档变更与应用镜像变更，错误地将根级 README 纳入 appstore 路径校验范围并报错。同类问题在历史模式11中已多次出现（如 PR #2512 中的 `.claude/agents/README.md` 路径校验失败）。

## 修复方向

### 方向 1（置信度: 高）
这是一个 **CI 假阳性（false positive）**，PR 代码变更本身没有问题。CI 的 appstore 发布规范预检工具需要增强过滤逻辑，在检测到被修改文件仅为仓库根级文档（如根目录 `README.md`、`README.en.md`）且不涉及任何应用镜像目录下的文件时，应跳过 appstore 路径校验。对于本 PR，无需修改任何代码或 Dockerfile，可直接忽略该 CI 失败告警或通过白名单机制放行。

### 方向 2（置信度: 低）
若 CI 工具暂不支持排除根级文档，可通过在仓库根目录配置文件中将 `README.md` 和 `README.en.md` 加入 appstore 检查的排除列表来规避。但此方向属于绕过 CI 工具缺陷而非修复根本问题，不建议作为长期方案。

## 需要进一步确认的点
- 确认 CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）中是否有针对根级非应用镜像文件的排除逻辑，若有则需排查为何此次未生效。
- 确认该仓库的 CI 配置中是否已有文件过滤/白名单机制，若有则需将根级 `README.md` / `README.en.md` 纳入白名单。

## 修复验证要求
本 PR 不涉及正则 patch 外部源文件，无需额外验证步骤。
