# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），`eulerpublisher` 工具对根级 `README.md` 的 appstore 路径校验出现误报，与 PR 代码变更无关。

## 修改的文件
无。该失败为 CI 基础设施问题，`eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑可能存在字符串规范化缺失（如缺少 `os.path.normpath` 或 `lstrip('/')` 处理），需要 CI 维护者排查，**无需修改仓库文件**。

## 修复逻辑
CI 分析报告确认：PR #2790 仅修改了 `README.md` 中"可用镜像 Tags"部分的版本列表内容（如将 `24.03-lts-sp2` 替换为 `24.03-lts-sp3`、新增 `25.09` 条目等），未新增文件、未变更文件路径，也未涉及任何 Dockerfile 或构建逻辑。CI 失败由 `eulerpublisher` 工具的 appstore 发布规范预检触发，对 `README.md` 报告 `[Path Error] The expected path should be /README.md`，但 `README.md` 确实位于仓库根目录，路径本身正确。根据规范，infra-error 不需要代码修改。

## 潜在风险
无。