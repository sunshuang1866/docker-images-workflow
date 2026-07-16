# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），`eulerpublisher` 的 appstore 路径校验逻辑对根级 `README.md` 存在误判。

## 修改的文件
无。PR 仅修改了 `README.md`（文档更新），与 CI 报出的 [Path Error] 无因果关系。

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 `eulerpublisher/update/container/app/update.py:273` 中的路径校验逻辑对仓库根目录的 `README.md` 产生了误报（期望路径 `/README.md` 与实际路径一致，但校验仍返回 FAILURE）。这是 CI 工具本身的缺陷，PR 代码无需修改，也无代码可修改。建议重新触发 CI 或联系 CI 维护者排查 `update.py` 中的路径校验规则。

## 潜在风险
无