# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根目录README路径误检
- 新模式症状关键词: Path Error, expected path should be, /README.md, update.py

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查器（`update.py`）对仓库根目录的 `README.md` 和 `README.en.md` 执行了路径校验，并错误地判定这两个文件不符合 appstore 发布路径规范（期望路径为 `/README.md`）。然而这些文件是仓库自身的项目文档，并非应用镜像的发布元数据，不应受 appstore 路径规范的约束。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2790 仅修改了根目录 `README.md` 和 `README.en.md` 中的镜像 Tags 列表（更新 `24.03-lts-sp2` → `24.03-lts-sp3`、新增 `25.09` 条目、补全 `24.03-lts-sp2` 独立行），这些是合法的文档维护变更。CI 失败是由 appstore 规范检查器对所有变更文件（包括根目录 README）进行路径校验的机制缺陷导致的误报，与 PR 的实际内容修改无关。

## 修复方向

### 方向 1（置信度: 高）
将根目录 `README.md` 和 `README.en.md` 加入 appstore 路径校验的白名单/排除列表，使 `update.py` 不对仓库根目录的文档文件进行 appstore 路径规范校验。文件可按文件名或路径做如下区分：
- 根目录下的 `README.md` / `README.en.md` 属于项目文档，不参与 appstore 路径校验
- 各应用镜像目录下的 README 文件（如 `AI/xxx/doc/README.md`）仍按现有规则校验

### 方向 2（置信度: 低）
若 CI 设计上要求所有 README 文件均通过路径校验，则需在 PR 中将 `README.en.md` 重命名为 appstore 期望的路径格式。但此方案不合逻辑——`README.en.md` 作为项目英文版 README 应保留在根目录，且 `README.md` 已在根目录但同样报错，说明校验逻辑本身存在问题。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中 appstore 路径校验逻辑：是否对所有变更文件（包括根目录文件）无条件执行路径校验，还是只针对特定目录（如 `AI/`、`Bigdata/` 等应用分类目录）进行校验。
- 确认 `README.md` 在根目录且文件名完全匹配期望路径 `/README.md` 时为何仍被判为 FAILURE——可能是路径比较时缺少根目录前缀（如期望 `/README.md` 但传入 `README.md`），需查看 `update.py` 的路径比较实现。

## 修复验证要求
无。此问题为 CI 基础设施层面（`update.py` 校验逻辑）的缺陷，与 PR 代码变更无关，不需要对源文件进行补丁修复。
