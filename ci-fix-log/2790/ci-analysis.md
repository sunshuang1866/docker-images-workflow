# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（变体）
- 新模式标题: -
- 新模式症状关键词: -

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），CI 的 appstore 发布规范预检工具 `update.py` 检测到 `README.md` 被修改，但该文件不在任何应用镜像的目录结构内，不符合 appstore 发布规范中对变更文件路径的要求，导致路径校验失败。

### 与 PR 变更的关联
PR 的改动仅为 `README.md` 和 `README.en.md` 中文档内容的更新（修正 tags 列表，将 `latest` 从 `24.03-lts-sp2` 改为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）。**未包含任何应用镜像的 Dockerfile、meta.yml 或其他镜像相关文件变更**。

CI 流水线为 appstore 发布流程，其预检阶段要求 PR 中所有变更文件都属于合法的应用镜像目录（如 `AI/`、`Bigdata/` 等下辖的 `{image-version}/{os-version}/` 结构）。根级 `README.md` 是项目级文档，不在任何镜像目录内，因此被校验工具拒绝。

## 修复方向

### 方向 1（置信度: 中）
将 README 文档更新合并到一个包含实际应用镜像变更的 PR 中提交（例如伴随某个应用镜像的新增或版本更新）。CI appstore 预检只会在 PR 中存在有效镜像变更时通过；纯文档 PR 不适合走该 CI 流水线。

### 方向 2（置信度: 低）
确认是否存在独立于 appstore 发布流水线之外的其他 CI 流程（如纯文档检查 pipeline），将此类纯文档 PR 路由至对应流程。若不存在，则需确认 docs-only PR 是否可以豁免 appstore 预检（需与 CI 维护团队确认流水线配置策略）。

## 需要进一步确认的点
1. CI 流水线是否有针对 docs-only PR 的豁免机制（如匹配 `update readme` 类标题跳过 appstore 预检）？
2. `update.py` 中路径校验逻辑的具体实现：是拒绝所有非 `{category}/{image}/{version}/{os}/` 路径下的文件，还是有白名单机制？
3. 该仓库的 CI 是否区分"应用镜像发布"和"项目文档维护"两种 PR 类型——若区分，需确认如何将本 PR 标记为后者。

## 修复验证要求
（本失败为 CI 流水线流程问题，不涉及正则 patch 外部源文件，无需额外验证步骤。）
