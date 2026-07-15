# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施逻辑缺陷（infra-error），与 PR #3153 的文档变更内容无关。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了根目录 `README.md`（和 `README.en.md`），更新可用基础镜像标签列表，属于纯文档变更。CI 流水线中的 appstore 路径校验工具 `eulerpublisher/update/container/app/update.py` 对所有 PR 的 diff 文件执行路径校验，要求修改的文件必须能映射到 appstore 镜像条目。根目录文档文件（`README.md`）不在任何场景目录（`Bigdata/`、`AI/` 等）下，也不在 `image-list.yml` 中，因此触发 `[Path Error]` 校验失败。

根因是 CI 工具缺乏对仓库级元数据文档文件的白名单豁免机制，而非 PR 代码存在问题。修复方向应当是修改 CI 管道代码（`update.py`）增加白名单，或更改 CI 配置以区分文档 PR 与镜像 PR，均不在原始 PR 变更文件范围内。按指令"分析报告指出是 infra-error 时，不强行改代码"，本项目代码无需任何修改。

## 潜在风险
无 — 未修改任何代码文件。