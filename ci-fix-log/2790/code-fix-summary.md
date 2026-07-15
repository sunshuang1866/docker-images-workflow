# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），由 appstore 预检工具（eulerpublisher update.py）的路径校验逻辑导致，与 PR 内容变更无关。

## 修改的文件
无。

## 修复逻辑
CI 分析报告明确指出：失败原因是 eulerpublisher update.py 在执行 appstore 发布规范预检时，对 `README.md` 路径格式校验失败，提示期望路径应为 `/README.md`（带前导 `/`），而工具内部解析出的路径为 `README.md`（无前导 `/`），导致路径格式误判。报告同时指出"本失败与 PR 内容变更无直接因果关联"。

PR 仅修改了 `README.md` 中的镜像 Tags 列表内容——将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3` 并新增 `25.09` 等条目，文件内容变更本身正确且合规。问题根源在于 CI 工作流中 eulerpublisher 工具的路径校验实现，不在本仓库代码范围内。

## 潜在风险
无。建议联系 CI/基础设施团队检查 eulerpublisher update.py 的路径校验逻辑是否需要兼容无前导 `/` 的路径格式，或重新触发 CI 运行以排除偶发故障。