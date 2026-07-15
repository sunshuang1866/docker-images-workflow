# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 发布路径校验逻辑未对根级纯文档文件（`README.md`）做豁免处理，导致纯文档更新的 PR 被误判为路径错误。

## 修改的文件
无。此 PR 的 `README.md` 变更是合法的文档更新（新增 tags 25.09、24.03-lts-sp3、24.03-lts-sp2 链接），不涉及任何镜像构建逻辑，源代码本身无 bug。

## 修复逻辑
根据分析报告，失败类型为 `infra-error`，根因是 CI 预检工具的路径校验规则将根级 `README.md` 纳入 appstore 镜像发布路径检查范围，而该文件是仓库的纯文档文件，不属于任何镜像分类目录。此类 CI 基础设施缺陷不应通过修改 PR 涉及的源文件来"修复"，而需要 CI 工具侧对根级文档文件添加白名单/豁免规则。

## 潜在风险
无。未修改任何源代码。