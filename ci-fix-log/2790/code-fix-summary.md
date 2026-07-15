# 修复摘要

## 修复的问题
CI appstore 发布规范检查工具对根目录 `README.md` 误报路径错误，属 CI 基础设置问题（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
1. CI 失败来自 `eulerpublisher/update/container/app/update.py` 中的 appstore 规范预检，该工具对根目录 `README.md` 报告了 `[Path Error] The expected path should be /README.md`。
2. `README.md` 的实际路径正是 `/README.md`（仓库根目录），错误信息与事实矛盾，判定为 **CI 检查工具的误报（false positive）**。该检查工具可能仅设计用于验证应用镜像子目录下的文件路径规范（如 `{category}/{image}/{version}/{os}/Dockerfile`），对根目录文件缺少豁免或正确匹配逻辑。
3. PR #2790 仅修改了 `README.md` 和 `README.en.md` 的文档内容（新增镜像 tags 条目），与 CI 失败无因果关系，源代码无 bug。
4. 实际修复需要在 `eulerpublisher/update/container/app/update.py` 中调整路径校验逻辑（对根目录文件做豁免处理），但该文件不在 `pr.changed_files` 范围内，且根据最小化修复原则，不应对 CI 工具进行跨仓库修改。
5. 根据修复原则："如果分析报告指出是 infra-error（CI 基础设施问题），无需代码修改，不强行改代码"。

## 潜在风险
无 — 此为 CI 工具误报，`README.md` 文档内容正确，合入后不会影响实际功能。