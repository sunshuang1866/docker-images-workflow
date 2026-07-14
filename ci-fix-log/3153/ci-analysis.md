# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根路径文件校验误报
- 新模式症状关键词: update.py, Path Error, README.md, expected path should be, appstore

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对本次 PR 中修改的根路径文件 `README.md` 执行路径校验，校验器报告 `[Path Error] The expected path should be /README.md`。然而 `README.md` 实际就在仓库根路径下（即 `/README.md`），路径本身与期望一致却仍然被判定为 FAILURE。推测 CI 校验工具在比对 git diff 中的路径（格式为 `a/README.md` 或 `b/README.md`）与预期路径 `/README.md` 时，`a/` 或 `b/` 前缀未被正确剥离，导致字面比较失败。

### 与 PR 变更的关联
本次 PR 为纯文档变更（仅修改 `README.md` 和 `README.en.md`，更新基础镜像可用 tag 列表），未修改任何 Dockerfile、meta.yml、image-list.yml 等应用镜像相关文件。CI 失败由校验工具对根路径文件进行路径比对时产生的误报导致，与 PR 变更内容本身的正确性无关。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `eulerpublisher/update/container/app/update.py` 中的路径比对逻辑未正确处理 git diff 的 `a/` / `b/` 前缀（或路径未做归一化），导致根路径文件 `README.md` 的路径比对产生误报。需要 CI 工具维护者修复该校验逻辑。此非本 PR 仓库代码层面可修复的问题，属于 infra-error，Code Fixer 无需处理。

### 方向 2（置信度: 低）
另一种可能性是 CI 校验工具对 `README.md` 的检查项仅适用于应用镜像子目录（如 `Bigdata/`、`AI/` 等），根路径 `README.md` 不应参与该检查。若校验脚本有黑白名单机制，将根路径 `README.*.md` 加入排除列表即可解决。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 222~273 行之间的路径校验逻辑具体如何实现，确认 `a/` / `b/` 前缀的处理方式。
- 该校验是否预期对根路径 `README.md` 执行（即 `README.md` 是否应纳入 appstore 发布规范检查范围）。
- PR 的实际流水线编号在 CI 日志中显示为 3184（分支 `fix/3153`），与上下文 PR 编号 3153 不一致，需确认是否为同一 PR 的不同流水线实例。
