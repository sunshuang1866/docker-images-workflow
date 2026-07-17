# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 前置检查——日志与状态一致性
CI 日志末尾为 `Finished: FAILURE`，日志状态与 PR 失败状态一致，继续分析。

### 直接错误
```
2026-07-16 20:34:19,171-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本（`update.py`）检测到仓库根目录的 `README.md` 发生变更后，对其进行路径格式验证，判定为 `[Path Error]`。该检查预期 `README.md` 位于仓库根路径 `/README.md`，而实际变更的 `README.md` 确实在根目录——此检查本不应作用于仓库根级文档文件，应仅针对应用镜像目录（如 `AI/xxx/…/README.md`）执行，故为 CI 校验脚本的误报。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #3153 仅修改了两个文件：`README.md` 和 `README.en.md`，均为纯文档更新——更新基础镜像可用 tag 列表（将 latest 从 sp2 升级至 sp4，新增 sp3/25.09/sp2 条目，同时修复了旧条目中 tag 名称与 URL 版本不一致的问题）。这些改动不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等应用镜像元数据文件，不应触发 appstore 发布规范校验。

## 修复方向

### 方向 1（置信度: 中）
CI 校验脚本 `eulerpublisher/update/container/app/update.py` 中的 diff 比对与路径校验逻辑未对仓库根级文件做豁免过滤，导致纯文档类 PR 的根级 `README.md` 被误判为 appstore 路径错误。问题出在 CI 工具端，而非 PR 代码变更端。若需修复，应从 CI 工具侧增加豁免逻辑：对不在任何 `image-list.yml` 管理范围内的根级文件跳过 appstore 路径校验。

### 方向 2（置信度: 低）
检查 `update.py` 的 diff 获取与路径匹配逻辑，确认是否存在路径拼接 bug（例如将根级文件误判到某个空路径拼接的前缀下），导致 `/README.md` 被错误地与其他路径模式做比较。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 222–273 行及第 356 行的 diff 检测与 spec 校验逻辑：需确认 diff 得出的 `README.md` 被传给哪个路径校验函数，以及该校验函数为何对根路径文件报错。
2. CI pipeline 中是否预期 appstore 校验 job 应在"有应用镜像文件变更"的条件下才触发——当前日志显示该 job 无条件运行（或条件判断有误）。
3. PR #3184（`sunshuang1866:fix/3153`，日志实际触发源）与 PR #3153 的关系：logs 中 upstream cause 为 PR 3184，而分析上下文指向 PR 3153，需确认两者 diff 是否完全一致。
