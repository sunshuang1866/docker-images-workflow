# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根 README 路径校验失败
- 新模式症状关键词: Path Error, expected path, README.md, appstore, release specification

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排脚本中的 appstore 发布规范预检步骤）
- 失败原因: CI 预检工具检测到根目录 `README.md` 发生变更，并将其纳入 appstore 发布规范校验流程。在校验过程中，工具记录的路径为 `README.md`（无前导斜杠的相对格式），而期望的路径为 `/README.md`（绝对格式），字符串对比不通过导致 `[Path Error]`。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件的内容（更新基础镜像可用 Tags 列表），未修改任何构建逻辑、Dockerfile 或目录结构。该 CI 检查失败并非由 PR 的变更内容本身引起，而是 CI 预检工具（`eulerpublisher`）在处理根目录文档变更时，路径格式化（归一化）策略与校验期望不匹配所致。任何涉及根目录 `README.md` 变更的 PR 都可能触发同类失败。

## 修复方向

### 方向 1（置信度: 低）
CI 预检工具 `eulerpublisher/update/container/app/update.py` 在构建被检查文件的路径时，未将根目录文件的路径格式化为 `/README.md`（带前导斜杠），导致与期望值不匹配。修复需在 CI 工具侧而非 PR 侧进行：在路径检测/对比逻辑中增加路径头部的斜杠统一规范化处理。

### 方向 2（置信度: 中）
此 CI 检查是为应用镜像 appstore 上架而设计的，根目录的仓库级 `README.md` 不属于应用镜像范畴，原本不应该被纳入 appstore 发布规范校验的范畴。修复方向为在 CI 工具的变更文件过滤逻辑中排除仓库根目录级别的通用文件（如根目录 README），使其仅对 `{场景}/{应用}/{版本}/{OS版本}/` 路径下的文件执行 appstore 规范校验。

### 方向 3（置信度: 低）
如果根目录 README 确实需要被校验（如基础镜像发布），则 CI 工具的期望路径 `/README.md` 是正确的，需确保传入的路径也使用前导斜杠的绝对路径格式。

## 需要进一步确认的点

1. CI 预检工具 `eulerpublisher` 的 `update.py` 中 `Difference` 列表构建和路径校验逻辑——确认路径是如何从 diff 中提取并传入校验函数的，以及为何根目录文件生成的路径缺少前导 `/`。
2. 根目录 README 是否应该纳入 appstore 发布规范校验范围——需确认这是预期行为还是工具 bug。如果是预期行为，需确认规范中根目录文件的路径应该是什么格式。
3. 上游 trigger job 日志显示触发了 "PR 3184 [sunshuang1866:fix/3153 → master]"，而非 PR 3153 本身，需确认本次 CI 运行日志是否确实对应当前 PR 3153，还是来自对 3153 的修复分支。

## 修复验证要求

本失败为 CI 工具侧的路径格式化问题，不涉及 Dockerfile 或项目代码修改。若决定在 CI 工具（`eulerpublisher` update.py）中修复路径规范化逻辑，code-fixer 必须：
1. 获取 `eulerpublisher` 当前版本的 `update.py` 源码，确认路径提取、差分列表构建和校验对比的完整调用链。
2. 在本地环境中用实际文件路径参数验证修改后的路径格式化逻辑，确保 `README.md` → `/README.md` 归一化不会对已有的应用镜像子目录路径（如 `Bigdata/spark/3.x/24.03-lts-sp4/README.md`）产生副作用。
