# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（延伸）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```
```
2026-06-29 15:21:37,042 - INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-29 15:21:41,552 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 `update.py` 检测到 PR 修改的两个文件 `README.en.md` 和 `README.md` 位于仓库根目录，不符合容器镜像 appstore 上架规范中期望的文件路径格式。该 CI 检查期望修改的文件位于容器镜像目录结构内（如 `Category/ImageName/version/os-version/Dockerfile`），而根目录的 README 文档文件不在 appstore 发布规范的允许路径范围内。

### 与 PR 变更的关联
- **PR 仅修改了 `README.en.md` 和 `README.md` 两个根目录文档文件**，更新了基础镜像 tags 表格中的版本信息（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，更新 `latest` 指向）。
- PR 变更内容本身没有问题（纯文档更新），但触发了一条专门验证 **appstore 容器镜像发布规范** 的 CI 流水线，该流水线的路径校验规则不允许根目录 README 文件变更。
- 这属于 CI 流程设计问题：纯文档类 PR 不应触发 appstore 发布规范检查流水线，或该流水线应豁免根目录 README 文件。

## 修复方向

### 方向 1（置信度: 中）
CI 配置层面：调整触发规则，使只修改根目录文档文件（`README.md`、`README.en.md` 等）的 PR 不触发 appstore 发布规范校验流水线（`eulerpublisher/update/container/app/update.py`），或在该校验工具中增加对根目录 README 文件的豁免逻辑。

### 方向 2（置信度: 低）
PR 内容层面：如果该 PR 确实不应仅为文档更新（即本应同时提交容器镜像相关文件），则需要补充对应的镜像 Dockerfile 或元数据文件变更。但从 PR 标题 `update readme.md` 来看，该 PR 意图就是纯文档更新。

## 需要进一步确认的点
- 确认 `update.py:273` 处的路径校验逻辑具体规则（期望的文件路径格式是什么），以判断是修改校验规则还是修改流水线触发条件更合理。
- 确认是否存在其他仅修改根目录文档文件的类似 PR 被 CI 拦截的案例（参考 模式11 中 `.claude/README.md` 路径校验失败的类似情况）。
- 确认该 appstore 校验流水线是否应该在所有 PR 上运行，还是仅限包含容器镜像目录变更的 PR。
