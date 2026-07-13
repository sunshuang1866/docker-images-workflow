# 修复摘要

## 修复的问题
CI appstore 发布规范预检将纯文档 PR 的根目录 README 文件标记为路径错误，属 CI 基础设施问题，无需修改 PR 中的源文件。

## 修改的文件
无。本次 CI 失败为基础设施/CI 配置问题（`eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑缺少对纯文档变更 PR 的豁免），不涉及 `pr.changed_files` 中 `README.en.md` 和 `README.md` 的代码错误。

## 修复逻辑
CI 分析报告（置信度：高）确认：PR #3153 仅修改了仓库根目录下的 `README.en.md` 和 `README.md` 两个文档文件（更新基础镜像可用 tags 列表），无任何 Docker 镜像构建文件变更。CI 的 appstore 预检脚本将这两个根目录文档文件与 Docker 镜像目录结构规范比对，判定路径错误。根因在于 `update.py` 缺少对纯文档变更 PR 的豁免机制，属于 CI 基础设施问题，应由 CI 维护方在 `update.py` 的差异分析阶段添加文件过滤逻辑，排除不在镜像目录下的纯文档文件。

PR 中 README 文件的变更内容（tags 列表 URL 更新）本身正确无误，无需修改。

## 潜在风险
无。本次未修改任何源文件。