# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式（关联参考: 模式11）
- 新模式标题: 根目录文件触发appstore路径校验
- 新模式症状关键词: Path Error, expected path, appstore, README.md, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检步骤）
- 失败原因: CI 工具 `eulerpublisher` 检测到 `README.md` 被修改后，运行了 appstore 发布规范预检。该检查期望被修改的文件遵循 appstore 镜像目录路径规范（如 `{category}/{image}/{version}/{os-version}/` 层级结构），但根目录下的 `README.md` 不属于 appstore 镜像条目，因此校验器报告 `[Path Error]` 并中止构建。

### 与 PR 变更的关联
- **PR 变更**: 仅修改了根目录的 `README.md` 和 `README.en.md`，更新基础镜像的可用 tag 列表（新增 24.03-lts-sp4/sp3/sp2、25.09 条目，修正已有条目的链接 URL）。
- **关联判定**: PR 的文档变更触发了 CI 的 appstore 发布规范预检。由于根目录 `README.md` 不是 appstore 镜像发布条目，CI 校验工具按规则将其标记为路径错误。**该失败不是 PR 代码逻辑错误引起的**，而是 CI 流水线对纯文档变更的执行了不适用于文档 PR 的 appstore 发布校验。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线在执行 appstore 发布规范预检前，应过滤掉非镜像目录的文件变更（如根目录 `README.md`、`README.en.md` 等纯文档文件）。若 `eulerpublisher` 的 `update.py` 在 diff 检测阶段已能区分"文档文件"与"镜像目录文件"，则应在预检阶段跳过文档文件，或仅在检测到镜像目录变更时才触发 appstore 校验。

### 方向 2（置信度: 低）
如果 CI 工具不支持自动区分文档文件与镜像文件，则此 PR 可能需要通过 CI 跳过机制（如 commit message 中加 `[skip ci]` 或 repo 配置中为 README-only PR 添加豁免规则）来规避误报。但这取决于项目的 CI 基础设施是否支持此类跳过策略。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近的校验逻辑：确认 `[Path Error]` 是如何产生的——是因为 `README.md` 不在 `image-list.yml` 的已知路径中，还是因为校验规则要求所有 PR 变更的根目录文件必须关联到某个 appstore 条目。
2. 该 CI 流水线是否对纯文档 PR 有其他处理策略——当前看来所有 PR 都会经过 appstore 预检，可能需要确认项目的 CI 设计意图。
3. 若 `eulerpublisher` 工具的路径校验逻辑中确实硬编码了"非 appstore 路径即报错"的规则，需确认修改 `update.py` 的权限和流程（该文件属于 CI 基础设施，可能不在本仓库的管理范围内）。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher/update/container/app/update.py` 的校验逻辑，code-fixer 必须：
1. 获取 `eulerpublisher` 工具的完整源码，理解第 273 行附近的路径校验逻辑和"expected path"的生成规则。
2. 在本地用同样的 diff 场景（仅包含根目录 `README.md` 变更）验证修改后的校验器不再报告 `[Path Error]`。
3. 确认修改不影响对真正的镜像目录路径（如 `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`）的校验结果。
