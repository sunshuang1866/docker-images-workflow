# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档变更误触路径校验
- 新模式症状关键词: README.md, Path Error, The expected path should be, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171 - update.py[line:356] - INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范检查工具（`update.py`）对变更文件 `README.md` 执行路径校验时报错 "The expected path should be /README.md"，但 `README.md` 实际就位于仓库根路径 `/README.md`，路径完全符合预期。该错误是 CI 检查工具对纯文档类 PR（仅修改 README 文件，不含任何 Dockerfile、meta.yml、image-info.yml 等镜像构建文件）产生的误报。

### 与 PR 变更的关联
PR 仅修改了两个文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tags 列表的文档内容（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，拆分 24.03-lts-sp2 独立条目）。这些变更**完全不涉及**任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 等镜像构建相关文件，属于纯文档类 PR。CI appstore 发布规范检查原本用于验证镜像提交 PR 的合规性，对纯文档变更 PR 不适用，产生了误报。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施误报（infra-error），与 PR 代码变更无关，**无需对 README.md 或任何仓库文件进行修改**。该 PR 为纯文档类变更，应跳过 appstore 发布规范检查。建议 CI 管理员在触发/调度层增加过滤逻辑：当 PR 仅变更仓库根目录的 README/文档文件且不含镜像构建文件时，跳过 appstore 规范校验步骤。

### 方向 2（可选，置信度: 中）
若 CI 调度层暂时无法修改，可尝试在 PR 中同时触发一个微小的镜像元数据变更（如在某个 `image-list.yml` 中补充注释），使 CI 的 appstore 检查有实际镜像条目可校验，避免路径校验误报。但此方向仅为权宜之计，不推荐。

## 需要进一步确认的点
- 确认 CI 调度器（`multiarch/openeuler/trigger/openeuler-docker-images`）是否有能力识别"仅文档变更 PR"并跳过下游的 x86-64/aarch64 appstore 校验 job
- 确认 `eulerpublisher` 工具的 `update.py` 中路径校验逻辑的具体实现（第 273 行附近），以理解为何 `/README.md` 被判定为路径错误
