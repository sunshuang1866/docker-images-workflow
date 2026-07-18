# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根目录文件被误检
- 新模式症状关键词: Path Error, expected path should be, appstore, README.md, eulerpublisher, update.py, 根目录

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检逻辑）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对 PR 中变更的仓库根目录 `README.md` 执行了镜像发布路径校验，但仓库根目录的 `README.md` 不属于任何应用镜像的发布目录，预检规则在此场景下产生误报 `[Path Error]`。

### 与 PR 变更的关联
**与 PR 变更间接相关，但并非代码错误。** 该 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 列表），属于纯文档维护。CI 的 appstore 预检流水线没有区分根目录文档变更和应用镜像发布变更，导致对不适用 appstore 规范的 `README.md` 误报了路径检查错误。

## 修复方向

### 方向 1（置信度: 高）
CI 工具（`eulerpublisher/update/container/app/update.py`）的 appstore 预检逻辑需要增加文件路径过滤：对位于仓库根目录（不在任何场景分类子目录如 `Bigdata/`、`AI/`、`Cloud/` 等下的文件）的文件跳过 appstore 发布规范校验，或将根目录 `README.*` 加入豁免列表。

### 方向 2（置信度: 中）
若 CI 工具本身无法修改，可考虑将此类纯文档 PR 通过 commit message 约定（如包含 `docs:` 前缀）来跳过 appstore 预检阶段。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py:356` 行的 `Difference` 计算逻辑：为何 `README.en.md` 未被列入差异列表而仅有 `README.md` 被检查；
2. 确认 CI 预检工具是否有配置文件可配置文件/目录豁免规则；
3. 确认该仓库的 CI 流水线设计意图：根目录的 `README.md` 变更是否应触发 appstore 发布规范预检；
4. 确认 `[Path Error] The expected path should be /README.md` 中的 `/README.md` 前缀 `/` 是否为绝对路径标注，还是预检工具内部路径拼接逻辑错误（如重复添加前缀）。
