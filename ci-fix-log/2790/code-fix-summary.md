# 修复摘要

## 修复的问题
CI appstore 预检工具检测到 PR 修改了 `README.en.md`，该文件不在 appstore 规范允许的变更路径（仅 `/README.md`）中，触发 Path Error 校验失败。

## 修改的文件
- `README.en.md`: 撤销 PR 对该文件的修改，恢复被删除的 `[24.03-lts-sp3]` 条目行，使文件回到修改前状态
- `README.md`: 保持不变（已正确移除了重复的 `24.03-lts-sp3` 条目）

## 修复逻辑
CI 分析报告指出 appstore 规范仅预期变更 `/README.md`，`README.en.md` 不属于允许变更路径。PR 同时修改了两个文件来移除重复的 tag 条目，导致校验失败。修复方案为：仅保留 `README.md` 的变更（移除重复条目），撤销 `README.en.md` 的变更，使英文 README 恢复原样。这样 CI 检查时仅检测到 `/README.md` 有变更，不再触发路径错误。

## 潜在风险
无。`README.en.md` 中恢复了重复的 `24.03-lts-sp3` 条目不影响功能，仅为文档的冗余条目。后续如需同步清理英文 README，可通过单独的文档 PR 处理。