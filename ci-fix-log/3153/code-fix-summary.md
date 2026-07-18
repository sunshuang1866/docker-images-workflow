# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error）：`eulerpublisher` 工具对纯文档 PR（仅修改根目录 `README.md`）执行了不适用的 appstore 发布路径校验，将不参与镜像发布的文档文件误判为 `[Path Error]`。

## 修改的文件
无。`README.md` 本身内容正确、不存在代码缺陷，不在允许修改的 `pr.changed_files` 范围之外的文件（如 CI 脚本 `eulerpublisher/update/container/app/update.py`）也不具备修改条件。

## 修复逻辑
CI 分析报告明确指出：该失败不是 PR 代码逻辑错误引起的，而是 CI 流水线在检测到文件变更后对所有文件执行 appstore 发布校验，未过滤掉根目录纯文档文件（如 `README.md`）。修复需要改动 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑（在 appstore 预检阶段跳过非镜像目录的文档文件），但该文件属于 CI 基础设施，不在本 PR 允许修改的文件列表内，且本任务禁止修改 `pr.changed_files` 之外的任何文件。

## 潜在风险
无。不从代码层面引入任何变更，不存在新增风险。建议由 CI 基础设施维护者处理：在 `update.py` 第 273 行附近的校验逻辑中添加文件路径过滤，或为纯文档 PR 配置 CI 跳过机制。