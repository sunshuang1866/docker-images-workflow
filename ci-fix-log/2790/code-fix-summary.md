# 修复摘要

## 修复的问题
CI appstore 发布规范预检误将纯文档 PR（仅修改 README.md）判定为路径校验失败。**此问题为 CI 基础设施配置问题，无需修改源代码文件。**

## 修改的文件
- 无代码修改。PR 变更的 `README.md` 内容本身正确，无需改动。

## 修复逻辑
CI 分析报告明确诊断：失败类型为 `lint-error`（实为 infra-error），根因是 CI 流水线的 appstore 路径校验工具（`eulerpublisher/update/container/app/update.py`）对根目录下的 `README.md` 文件触发了路径格式检查，而该检查仅适用于应用镜像子目录（如 `AppName/Version/Dockerfile`）。PR #2790 仅更新了 README.md 中的镜像 Tags 列表，属于纯文档类变更，不涉及任何应用镜像。

实际修复方向：需由 CI 管理员在流水线配置中将 `README.md`、`README.en.md` 等根目录文档文件加入 appstore 路径校验的排除列表/白名单，使其在仅修改文档时不触发该检查。此修复超出当前允许修改的文件范围（仅限 `README.md`），也无法通过修改源代码解决。

## 潜在风险
无。`README.md` 的文档内容变更完全安全，不存在代码层面的风险。