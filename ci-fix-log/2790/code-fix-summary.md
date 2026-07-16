# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（CI 基础设施问题），而非 PR 代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败原因是 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）在路径校验时，将 git diff 产出的相对路径 `README.md` 与期望的绝对路径 `/README.md` 做字符串比对，因缺少前导 `/` 导致路径匹配失败。这是 CI 工具的路径归一化缺陷，属于 infra-error。

PR #2790 仅修改了 `README.md` 和 `README.en.md` 两个文档文件（新增 24.03-lts-sp3、25.09 等镜像 tag 条目，更新 latest 标签），不涉及任何 Dockerfile 或构建逻辑变更，文档变更本身合法且正确。CI 在构建/编译阶段也未报任何错误。

**结论：问题根源在 CI 工具侧，需要由 CI 维护团队修复 `eulerpublisher/update/container/app/update.py` 中的路径归一化逻辑。PR 代码无需任何修改。**

## 潜在风险
无（未对任何源代码文件进行修改）