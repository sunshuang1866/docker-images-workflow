# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无需填写，已有匹配)
- 新模式症状关键词: (无需填写，已有匹配)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: CI 发布规范预检阶段 — `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具检测到 `README.md` 文件变更，并对其执行了路径合规性检查。该检查判定根目录下的 `README.md` 不符合 appstore 镜像发布的目录结构规范（该规范要求变更文件位于 `{镜像分类}/{镜像名}/{版本}/{os-版本}/` 或 `{镜像分类}/{镜像名}/doc/` 等约定的镜像目录层级下），因此报 Path Error。

### 与 PR 变更的关联
**强关联**。本次 PR 仅修改了根目录下的 `README.md` 和 `README.en.md`（更新 Tags 列表信息），属于仓库级文档维护。由于 CI 流水线对 PR 统一执行 appstore 发布规范预检，而这两个文件不在任何镜像发布目录结构内，触发了路径校验失败。PR 没有附带任何 Dockerfile、meta.yml、image-info.yml 等镜像发布所需文件，因此该检查必然失败。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 预检工具 `eulerpublisher/update/container/app/update.py` 应将仓库根目录下的 `README.md`、`README.en.md` 等非镜像发布文件纳入白名单/跳过列表，避免对此类纯文档变更执行镜像发布路径校验。这需要对 CI 编排逻辑或 `update.py` 的 `Difference` 过滤逻辑进行修改。

### 方向 2（置信度: 低）
如果 CI 确实要求所有 PR 都必须包含合法的镜像发布内容，则本次 PR 不应仅修改根目录 README，而应将 README 更新作为某个镜像发布 PR 的附属变更一并提交。但考虑到这是仓库根级文档维护，此方向不符合实际业务需要。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 `Difference` 提取逻辑是否对非镜像目录文件做了过滤——当前日志显示仅识别到 `README.md` 变更就进入了 appstore 校验流程。
2. 该 CI 流水线（`multiarch/openeuler/trigger/openeuler-docker-images`）的触发条件是否允许纯文档变更 PR，还是只应被包含镜像发布内容的 PR 触发。
3. 同一流水线的下游架构构建 job（x86-64、aarch64）是否有独立日志可进一步确认失败范围。
