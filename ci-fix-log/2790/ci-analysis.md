# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 扫描 PR diff 后发现 `README.md` 被修改，对其执行 appstore 发布路径校验时认定 `/README.md` 路径不符合 appstore 镜像发布规范（appstore 要求变更文件位于分类目录如 `AI/xxx/...` 下，而非仓库根目录）。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新可用镜像 Tags 列表，新增 `24.03-lts-sp3`、`25.09` 等条目），属于纯文档更新。无 Dockerfile、meta.yml、image-info.yml 或其他应用镜像相关文件变更。CI 的 appstore 发布预检流程将根级 README 变更误判为需要校验的 appstore 发布项，触发了路径校验失败。

## 修复方向

### 方向 1（置信度: 高）
此 PR 是纯文档更新（仅在 README 中补充新版本 Tag 链接），不应触发 appstore 发布规范检查。问题出在 CI 编排层：当 PR 仅包含根级文档变更（不涉及任何 `{Category}/{ImageName}/...` 路径下的镜像提交文件）时，CI 应跳过 appstore 发布校验步骤。需要在 CI pipeline 或 `eulerpublisher` 工具中增加对"纯文档 PR"的识别和跳过逻辑。

### 方向 2（置信度: 中）
若 CI 流水线无法修改，可考虑将根级 README 更新以单独 PR 提交到不触发 appstore 检查的分支或使用不同的 merge request 目标。

## 需要进一步确认的点
- 确认该 CI 流水线 (`multiarch/openeuler/x86-64/openeuler-docker-images`) 是否对所有 PR 均执行 appstore 校验，或是否有条件筛选（如仅对包含 `meta.yml`/`Dockerfile` 变更的 PR 触发校验）。
- 确认 PR 创建时是否误选了触发 appstore 发布流程的 MR target/分支。

## 修复验证要求
无需验证。此 PR 不涉及代码修复，问题在 CI 编排层面。PR 变更内容（README 文档更新）本身无错误。
