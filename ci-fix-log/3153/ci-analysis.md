# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具检测到 `README.md` 发生变更，对其执行路径校验时判定失败。日志 `Difference: ["README.md"]` 说明工具识别到了根目录 `README.md` 的变更，但该校验工具的检查逻辑是为应用镜像子目录（如 `AI/foo/…`、`Bigdata/bar/…`）设计的，不适用于仓库根目录的纯文档文件。根目录 `README.md` 的变更被误判为不满足 appstore 路径规范。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录下的两个文档文件：`README.md` 和 `README.en.md`。变更内容为更新基础镜像可用 Tags 列表（新增 24.03-lts-sp4、sp3、sp2、25.09 等条目，调整 latest 指向）。这些是合规的文档维护操作，不涉及任何应用镜像构建文件（Dockerfile、meta.yml、image-list.yml 等）。CI 的 appstore 规范检查本应针对应用镜像类变更执行，对纯文档类 PR 触发的检查属于 CI 工具的误报。

## 修复方向

### 方向 1（置信度: 中）
此为 CI 基础设施工具误报（infra-error），与 PR 代码变更无关。CI 的 appstore 规范预检工具（`update.py`）在扫描变更文件时，应将仓库根目录的纯文档文件（`README.md`、`README.en.md` 等）排除在路径规范校验范围之外，仅对位于应用镜像子目录内的文件执行路径校验。无需修改 PR 中的任何文件。

### 方向 2（置信度: 低）
若 CI 工具设计上确实要求所有 PR（包括纯文档类 PR）通过 appstore 路径校验，则该 PR 需要配套提交一个满足 appstore 规范的变更（如在某个应用镜像目录下新增/修改文件），以使预检通过。但从 PR 标题和 diff 内容判断，这种可能性较低。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 中路径校验的具体逻辑——是否对所有变更文件（包括根目录文件）无差别执行 appstore 路径规范检查，还是存在白名单/过滤机制但未正确处理本次场景。
- 该 CI job 是否有意对所有触及仓库根目录 `README.md` 的 PR 执行 appstore 规范检查，还是一次意外的误触发。
- `README.en.md` 同样被修改但未出现在 `Difference` 列表和检查表中——需要确认 CI 工具是否只校验中文 `README.md` 还是因为两文件在不同检项中。
