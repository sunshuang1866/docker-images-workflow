# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 CI 基础设施（infra-error）—— 预检工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑对仓库根目录 `README.md` 产生误报（期望 `/README.md` 格式），与 PR 对 `README.md` 的内容变更无关。

## 修改的文件
无。PR 仅修改 `README.md`（更新 Tags 列表），文件内容本身无问题，不存在需要修复的代码缺陷。

## 修复逻辑
1. CI 失败发生在 appstore 发布规范预检阶段，由 `update.py:273` 的路径校验触发。
2. 校验逻辑将 `README.md`（无前导 `/`）与预期格式 `/README.md` 匹配，导致 `[Path Error]` 误报。
3. 该问题根因在 CI 工具内部，不在本 PR 变更范围内，也不在允许修改的文件列表中。修复需调整 `eulerpublisher` 预检脚本的路径规范化/匹配逻辑，属于 CI 基础设施层面工作，不涉及源码仓库的 `README.md`。

## 潜在风险
无。`README.md` 未做任何修改，不引入任何风险。