# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根文件路径校验误报
- 新模式症状关键词: [Path Error], The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具内部）
- 失败原因: CI 的 `eulerpublisher` 工具对所有 PR 执行 appstore 发布规范校验。该 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（基础镜像 tag 文档更新），但 appstore 校验逻辑对变更文件执行路径格式比对时，发现 `README.md`（无前导 `/` 的相对路径形式）与期望的 `/README.md`（带前导 `/` 的绝对路径形式）不匹配，从而报告 `[Path Error]`。这属于 CI 工具路径规范化缺陷——根目录文件在 appstore 校验流程中被误判为路径格式错误。

### 与 PR 变更的关联
PR 变更内容与失败**无实质关联**。PR 仅更新了 README.md 和 README.en.md 中的基础镜像可用 tag 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`，并修正 latest 链接指向 SP4），属于纯文档维护。CI 的 appstore 发布规范校验不应适用于仓库根目录的文档类文件，本次失败是 CI 基础设施层面的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的路径校验逻辑存在缺陷：在对 PR 变更文件执行 appstore 发布规范校验前，未过滤掉仓库根目录的非应用镜像文件（如 `README.md`、`README.en.md`）。应在校验入口处增加白名单/黑名单过滤，将根目录文档文件排除在 appstore 规范校验范围之外。

### 方向 2（置信度: 低）
CI 编排层错误地将文档类 PR 路由到了 appstore 发布校验 job。应在 trigger 层的 PR 分类逻辑中判断 PR 是否为纯文档更新，若是则跳过 appstore 校验流程。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行的具体校验逻辑——该处是如何构造文件路径进行比较的，为什么 `README.md` 与 `/README.md` 会被判定为不匹配。
2. CI trigger 层的 PR 路由规则——是否所有 PR 均无条件触发 x86-64 下游 job 并执行 appstore 校验，还是存在按文件类型筛选的逻辑。
3. 该问题是否为已知的 CI 工具 bug，是否存在已有的修复分支或 issue。
