# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具 `update.py` 从 git diff 中解析出变更文件路径为 `README.md`（无前导斜杠），而工具内部期望的路径格式为 `/README.md`（带前导斜杠），路径格式不匹配导致校验失败。该 PR 仅修改了仓库根目录下的两个 README 文档（`README.md` 和 `README.en.md`），内容变更本身（更新基础镜像支持的 Tags 列表）无格式问题。

### 与 PR 变更的关联
PR 的改动（更新 README 中 base image tags 表格）本身是正确的文档维护工作：将过时的 tag `24.03-lts-sp2`（却指向 SP1 的 URL）修正为实际的 `24.03-lts-sp4`（指向正确的 SP4 URL），并补充了新 tag 条目。失败并非由 PR 内容错误导致，而是 CI appstore 校验工具在处理根目录文件路径时存在前导 `/` 格式不匹配的严格检查。

## 修复方向

### 方向 1（置信度: 低）
不需要修改 PR 内容。PR 的文档变更（README.md / README.en.md）本身正确，无需调整。该失败是 CI 工具 `update.py` 对路径格式的解析不一致所致——工具期望 `/<path>` 格式但实际接收 `/<path>` 缺失前导 `/` 的格式。需由 CI 维护方修复 `update.py` 中路径格式的统一处理逻辑，或为纯文档 PR（无 Dockerfile / meta.yml / image-info.yml 变更）跳过 appstore 发布规范预检。

### 方向 2（置信度: 低）
如果 CI 工具要求变更文件路径必须以 `/` 开头是硬性约束（而非 bug），则可能是 PR 分支的 git diff 输出格式问题，或工具在对 git diff 输出做路径提取时未对根目录路径做 `/` 前缀补全。需确认 `update.py` 中路径提取逻辑（`line:222` 附近 clone 后 diff 的路径解析）是否遗漏了对根目录一级文件的前导 `/` 处理。

## 需要进一步确认的点
1. 日志中显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，但上下文指定 PR 编号为 3153。需要确认本次 CI 日志是否确实对应 PR #3153，或是上游 trigger job 混合了多个 PR 的构建。
2. 需要获取 `eulerpublisher/update/container/app/update.py` 源码（尤其是第 222 行附近 clone 及 diff 解析逻辑，以及第 273 行路径校验逻辑），确认路径前导 `/` 的期望来源是什么——是从 git diff 中提取路径时本应带 `/` 但被错误剥离，还是工具内部硬编码了 `/` 前缀而输入未包含。
3. CI 日志中仅有一条 `README.md` 的 diff 记录，未看到 `README.en.md` 的路径出现在 diff 列表中（日志 INFO 只输出 `["README.md"]`）。需确认 `update.py` 的 diff 扫描是否遗漏了 `README.en.md`，以及这是否影响了检查结果。
