# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 ... update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对 PR 中变更的 `README.md` 执行路径校验时失败。PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新：调整支持的镜像 Tags 列表），但 CI 的 appstore 发布规范检查将根级 `README.md` 作为检查项，路径校验判定未通过。

### 与 PR 变更的关联
PR 变更仅涉及根级 `README.md` 和 `README.en.md` 的 Tags 列表更新，属于纯文档修正，不应触发 appstore 镜像发布规范检查。CI 的 `eulerpublisher` 工具检测到 `README.md` 被修改后，将其纳入 appstore 发布规范校验流程，而根级 README 文件不符合应用镜像的路径规范（`{category}/{image}/{version}/{os-version}/`），导致 `[Path Error]` 被标记为 FAILURE。PR 内容本身无错误，失败由 CI 预检逻辑覆盖范围过宽引起。

## 修复方向

### 方向 1（置信度: 中）
此 PR 为纯文档修改（根级 README 的 Tags 列表更正），不涉及任何应用镜像的新增或变更。CI 的 appstore 规范检查不应将根级 README 文件纳入校验范围。建议在 CI 的 `eulerpublisher` 工具中增加文件路径过滤逻辑，当变更文件仅为仓库根级文档（`/README.md`、`/README.en.md` 等）时跳过 appstore 发布规范检查，或在此类 PR 上不触发该检查 job。若 CI 配置无法修改，则需确认此类文档 PR 是否应走不同的 CI 流水线。

### 方向 2（置信度: 低）
如果 CI 工具的 `[Path Error] The expected path should be /README.md` 是通过路径字符串精确匹配产生的（即期望值为 `/README.md` 而实际比较值为 `README.md`），可能为 CI 工具中路径规范化处理的差异（缺少/多余的 `/` 前缀）。此方向需要查阅 `update.py:273` 附近的路径比较逻辑以确认。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py:273` 处的具体路径校验逻辑，确认 `[Path Error] The expected path should be /README.md` 的判断依据（字符串精确匹配 vs 模式匹配 vs 其他规则）。
- 确认 CI 流水线中 appstore 规范检查 job 是否有文件路径白名单机制，根级文档文件是否应被排除。
- 确认是否只对应用镜像目录（`AI/`、`Bigdata/`、`Cloud/` 等）下的变更才应触发 appstore 规范检查。
