# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档变更触发appstore校验
- 新模式症状关键词: Path Error, expected path, appstore, update.py, README.md, specification errors

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489 - INFO: Difference: [
    "README.md"
]
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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 中变更了根路径下的 `README.md`，该文件路径不符合 appstore 应用镜像的路径规范（期望格式为 `{category}/{image-name}/{version}/{os-version}/Dockerfile` 等），触发 "Path Error" 并导致 CI 失败。实际上该 PR 仅修改了项目根目录的 README.md 和 README.en.md 文档文件，属于纯文档变更，不应受 appstore 镜像路径校验规则约束。

### 与 PR 变更的关联
PR 变更仅限于 `README.md` 和 `README.en.md` 两个项目根目录文档文件的第 23 行区域（更新基础镜像可用 tags 列表，新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，保留 `24.03-lts-sp2`）。PR 未修改任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件，但 CI 的 `update.py` appstore 发布校验工具在 diff 扫描到 `README.md` 变更后，将其纳入 appstore 路径规范检查，导致误报 "Path Error"。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施侧修复：`eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范校验逻辑应增加文件过滤规则，排除项目根目录的文档文件（如 `README.md`、`README.en.md`、`LICENSE` 等），使其不受应用镜像路径格式的校验。此问题与 PR 代码变更无关，PR 提交者无需修改文档内容。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `update.py` 的路径校验白名单/黑名单逻辑是否可配置（即是否已有机制允许根目录文档文件豁免 appstore 路径检查）。
- 确认相同仓库中历史是否也有纯文档 PR 被同样拦截的记录（历史知识库中未见根目录 README 被拦截的案例，但模式 11 中有 `.claude/README.md` 路径校验失败的相似场景）。
