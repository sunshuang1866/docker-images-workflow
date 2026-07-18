# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为 infra-error，CI 的 appstore 发布规范预检工具 (`eulerpublisher/update/container/app/update.py`) 将纯文档 PR 的根级 README 变更误判为需要校验的 appstore 发布项，触发了路径校验失败。

## 修改的文件
无。PR 仅修改了 `README.md`（补充新版本镜像 Tag 链接），文件内容本身无错误，无需对代码进行任何修改。

## 修复逻辑
CI 失败分析报告明确指出：PR #2790 为纯文档更新（仅更新 README 中的可用镜像 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-list.yml 等应用镜像发布相关文件。CI 的 appstore 发布校验流程将根级 README 变更错误地纳入校验范围，属于 CI 编排层面的问题，应在 CI pipeline 或 `eulerpublisher` 工具中增加对"纯文档 PR"的识别和跳过逻辑。源码本身无需修复。

## 潜在风险
无。PR 变更内容（README 文档更新）正确无误，不涉及任何代码层面的风险。