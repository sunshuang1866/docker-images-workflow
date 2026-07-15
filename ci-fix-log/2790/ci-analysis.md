# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (eulerpublisher) 对 PR 中变更的仓库根层级 `README.md` 执行了路径校验，报出 `[Path Error] The expected path should be /README.md`。该 PR 仅涉及项目级文档文件（`README.md` 和 `README.en.md`）的 Tag 更新，不涉及任何应用镜像的 Dockerfile 或元数据，但 CI 工具仍将其纳入 appstore 发布路径规范检查范围，导致校验失败。

### 与 PR 变更的关联
PR 的变更内容仅为：
- 在 `README.md` 和 `README.en.md` 中将 `24.03-lts-sp2` 行更新为 `24.03-lts-sp3`（newest/latest Tag）
- 新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 的 Tag 条目及对应链接

这些变更均为合法的文档更新，不存在格式错误或内容问题。CI 失败源于 CI 工具对非镜像目录层级的文档文件执行了 appstore 路径格式校验，属于 CI 工具校验范围过度的问题。与 PR 代码内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对仓库根层级的非镜像文档文件（`README.md`）执行了路径校验。该工具应仅对 `image-list.yml` 中注册的镜像最小目录单元内的文件（如 `Bigdata/*/`、`AI/*/` 等分类目录下的 `README.md`）执行路径格式检查，而不应对仓库根层级的项目文档进行校验。确认是否需要调整 CI 工具的校验范围逻辑。

### 方向 2（置信度: 低）
若路径格式比较逻辑存在 `/` 前缀的严格匹配问题（即工具期望 `/README.md` 但实际传入 `README.md`），属于 CI 工具内部路径规范化处理的 bug，不是 PR 侧应修复的问题。

## 需要进一步确认的点
- 该 PR 是纯文档更新（修改仓库根层级的 `README.md` 和 `README.en.md`），不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 变更。若 CI 对这类 PR 的预期行为是允许通过，则当前失败属于 CI 工具误报（false positive），需在 CI 工具侧修复校验范围逻辑。
- 确认仓库根层级的 `README.md` 是否被 `image-list.yml` 或任何 CI 配置误注册为镜像最小目录单元。若被误注册，应从 `image-list.yml` 中移除。
- 确认 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑（line 273 附近以及其调用链上游的 diff 检测逻辑 line 356）对仓库根层级文件的处理策略。

## 修复验证要求
（无需填写——本失败为 infra-error，与 PR 代码变更无关，不存在需要 code-fixer 提交的修复。）
