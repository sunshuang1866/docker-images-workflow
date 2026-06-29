# 修复摘要

## 修复的问题
CI appstore 路径规范预检对仓库根目录下的纯文档文件（`README.md`、`README.en.md`）进行了误报，属于 CI 基础设施误判（infra-error），PR 修改的文件内容本身正确无误。

## 修改的文件
无需代码修改。

## 修复逻辑
CI 失败根因在 `eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑——该校验预期只对应用镜像子目录（如 `AI/`、`Bigdata/` 等）下的文件执行路径规范检查，但当前实现未排除仓库根目录级别的文件，导致仅修改 `README.md` 和 `README.en.md` 的文档类 PR 被错误标记为失败。

PR 变更的 `README.md` 和 `README.en.md` 内容（新增版本标签条目）正确无误，无需任何代码层面的修改。真正的修复应在上游 CI 工具 `update.py` 中增加根目录文件过滤逻辑，但该文件不在本 PR 允许修改的文件范围内。

## 潜在风险
无——本 PR 未修改任何源代码文件，`README.md` 和 `README.en.md` 的文档变更不会影响任何功能或构建流程。