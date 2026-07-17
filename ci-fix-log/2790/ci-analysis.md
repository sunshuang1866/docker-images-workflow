# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具，非仓库内文件）
- 失败原因: CI 的 appstore 发布规范校验器（`eulerpublisher`）检测到 PR 修改了根目录的 `README.md`，将其按应用镜像路径规范进行校验，由于 `README.md` 位于仓库根目录（而非 `{category}/{image}/{version}/{os-version}/` 层级结构下），校验失败。

### 与 PR 变更的关联
**PR 变更本身有效，不触发此错误。** PR #2790 仅修改了仓库根目录的两个文档文件：
- `README.md` — 更新可用镜像 Tags 表格（将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3` 作为 latest，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）
- `README.en.md` — 同上变更

这两个文件均未涉及任何 Dockerfile、`meta.yml`、`image-info.yml` 或其他应用镜像构建/发布相关文件。CI 失败是由于 Jenkins 流水线将文档类 PR 路由到了 appstore 发布规范校验 Job（`multiarch/openeuler/x86-64/openeuler-docker-images`），该 Job 的设计目的是校验应用镜像的目录结构和元数据是否符合上架规范，不应处理纯文档修改的 PR。

## 修复方向

### 方向 1（置信度: 中）
此为 CI 流水线路由问题（infra-error），**无需修改 PR 中的任何代码**。需要在 Jenkins 流水线的 trigger 层添加过滤逻辑：当 PR 仅修改仓库根目录的文档文件（如 `README.md`、`README.en.md`）且不涉及任何应用镜像目录时，跳过 appstore 发布规范校验 Job（`multiarch/openeuler/x86-64/openeuler-docker-images` 及对应的 aarch64 Job），直接标记为成功。

## 需要进一步确认的点
1. Jenkins 流水线 trigger 层（`multiarch/openeuler/trigger/openeuler-docker-images`）的触发条件配置——确认为何仅修改根级 README 的 PR 也会触发下游 x86-64 构建/校验 Job
2. `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑（line 273 附近的路径匹配规则），确认是否有方法让校验器识别并跳过仓库根目录文档
3. 是否存在其他仅修改根级文档但成功通过的 PR（用于对比 trigger 条件差异）

## 修复验证要求
无需验证——此失败与代码变更无关，修复措施在 CI 流水线配置层面（Jenkinsfile / pipeline 脚本），不属于本 PR 或本仓库的文件修改范围。
