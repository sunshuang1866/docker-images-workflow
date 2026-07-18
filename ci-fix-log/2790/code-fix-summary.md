# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），非源码错误。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出 PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新），不包含任何 appstore 容器镜像发布所需的文件。CI 流水线中的 `eulerpublisher` appstore 上架规范检查器对所有 PR 执行路径校验，发现 `README.md` 位于仓库根目录（`/README.md`），不符合 appstore 上架文件的预期路径结构（如 `{Category}/{ImageName}/{Version}/{OSVersion}/Dockerfile`），因此报告 `[Path Error]` 并标记构建失败。

这与 `README.md` 的内容正确性无关，`README.md` 本身无需修改。问题出在 CI 基础设施层面——`eulerpublisher/update/container/app/update.py` 对纯文档 PR 缺乏豁免机制。该文件不在 PR 变更范围内（`pr.changed_files = ['README.md']`），且属于 CI 编排工具内部代码，不应在此修复中修改。

## 潜在风险
无。未修改任何源码文件。