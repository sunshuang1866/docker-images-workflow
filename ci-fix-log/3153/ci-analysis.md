# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具内，非 PR 代码）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 变更进行了路径校验，检测到 `README.md` 发生变更，但在路径格式比对时失败——git diff 输出的文件路径为 `README.md`（无前导 `/`），而校验逻辑期望的路径格式为 `/README.md`（带前导 `/`），两者字符串不完全匹配导致校验未通过。

### 与 PR 变更的关联
PR #3153 是一个纯文档更新 PR，仅修改了仓库根目录的两个 README 文件：
- `README.md`：更新基础镜像可用 Tags 列表（将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签行）
- `README.en.md`：与 `README.md` 内容一致的同步骤更新

PR 未涉及任何 Dockerfile、meta.yml、image-list.yml、image-info.yml 或应用镜像构建文件。CI 的 appstore 预检对根级 README 变更触发了路径校验，而 CI 工具的路径比较逻辑存在格式不一致（缺少前导 `/`），导致纯文档 PR 被误判为 appstore 规范违规。此次失败与 PR 代码内容无实质关联。

## 修复方向

### 方向 1（置信度: 中）
CI 编排工具 `eulerpublisher/update/container/app/update.py` 中路径比较逻辑缺少路径标准化（normalization）。该工具在比对 git diff 输出的文件路径时，diff 输出不带前导 `/`（如 `README.md`），而工具内部期望的路径格式带前导 `/`（如 `/README.md`）。需要在 `update.py` 中对比对双方的路径名添加统一的前缀标准化处理（如 `os.path.normpath` 或统一添加/去除前导 `/`），使两种表示方式可以正确匹配。

**注意**：`update.py` 位于 CI 编排工具 `eulerpublisher` 仓库中，不在本 PR 的 openEuler-docker-images 仓库内。本仓库的 PR 提交者可能无法直接修改该文件。

### 方向 2（置信度: 低）
当前 PR 仅涉及根级 README 文档更新，理论上不应触发 appstore 发布规范预检。CI 触发条件可能需要增加过滤逻辑：当 PR 变更文件仅位于仓库根目录（非 `Bigdata/`、`AI/`、`Database/` 等应用镜像类别目录下）时，跳过 appstore 路径规范检查。此修复同样位于 CI 编排工具侧。

## 需要进一步确认的点

1. **CI 工具路径比较逻辑源码**：需要查看 `eulerpublisher/update/container/app/update.py` 中第 222-273 行附近的路径校验实现，确认路径比较时是否对 git diff 输出的文件名做了前导 `/` 标准化。
2. **`README.en.md` 未被检测的原因**：CI 日志检测到变更列表仅包含 `README.md`，但 PR diff 同时修改了 `README.en.md`。需要确认 CI 是否有意过滤了 `.en.md` 文件，或 git diff 范围存在偏差。
3. **是否为 CI 已知问题**：历史模式 11 中 PR #2512 的多个条目展示了类似的 appstore 路径校验失败案例（涉及 `.claude/README.md`），本案例可能是同一 CI 工具的同一类路径比较缺陷。
4. **eulerpublisher 仓库归属**：`eulerpublisher` 是 CI 编排工具的独立仓库，修复本错误需要在该仓库中提交变更，而非在本 PR 的 docker-images 仓库中操作。

## 修复验证要求
本案例的修复方向均指向 CI 编排工具本身（`eulerpublisher` 仓库），而非此 PR 中的文件。若选择修复方向 1，code-fixer 需要：
1. 获取 `eulerpublisher` 工具仓库源码（确认 CI 使用的版本分支）；
2. 在 `eulerpublisher/update/container/app/update.py` 中找到路径比对逻辑；
3. 添加路径标准化处理并验证修复后 `README.md` 与 `/README.md` 可以正确匹配；
4. 在 CI 环境中验证修复不会引入其他路径校验的回归问题。
