# 修复摘要

## 修复的问题
CI appstore 发布规范预检错误拒绝了纯文档 PR（仅修改根目录 README.md 和 README.en.md），属于 CI 基础设施策略问题，非源码缺陷。

## 修改的文件
- 无代码修改。

## 修复逻辑
该 PR (#2790) 仅更新了仓库根目录下的 `README.md` 和 `README.en.md` 中的基础镜像 Tags 列表（新增 `24.03-lts-sp3`、`25.09` 等），属于纯文档更新。CI 的 appstore 预检流程（`eulerpublisher/update/container/app/update.py`）要求变更文件必须位于 appstore 合法目录路径（如 `Bigdata/`、`AI/` 等）下，根目录 README 文件不在该白名单中，导致检查失败。

根因分析报告明确指出：「这不是代码错误，而是 CI 策略冲突——CI 的 appstore 预检流程不适合纯文档更新的 PR」。README 文件内容本身完全正确，无需修改。

此问题需要在 CI 侧解决：
1. 在 `update.py` 中为根目录文档文件添加白名单豁免
2. 或为纯文档 PR 设置免检通道

由于 CI 配置文件不在本 PR 的 `changed_files` 范围内（仅 `README.en.md` 和 `README.md`），无法通过修改 PR 文件解决此 CI 失败。

## 潜在风险
无。README 文件内容正确，未做任何代码变更，不会引入新风险。