# 修复摘要

## 修复的问题
无需代码修改——CI 失败属于基础设施配置问题（CI pipeline 将仅含根级 README 文档更新的 PR 错误地路由到了 appstore 镜像发布路径校验，触发文件路径不在白名单内的报错），无法通过修改 `README.md` 或 `README.en.md` 的内容解决。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告指出：
- PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，内容是纯文档维护（新增 `25.09`、`24.03-lts-sp3` 等版本标签条目），不包含任何 Dockerfile、meta.yml、image-info.yml 等镜像构建相关文件。
- 失败位置在 `eulerpublisher/update/container/app/update.py:273` 的 appstore 规范预检步骤，该校验期望所有 PR 修改文件位于可识别的镜像路径（如 `AI/`、`Bigdata/`、`Cloud/` 等场景目录）下，根级 README 不在白名单中因此被拒绝。

根因是 **CI 流水线未区分镜像构建 PR 与文档维护 PR**，将纯文档类 PR 也路由到了 appstore 路径校验。修正方向应是调整 CI 流水线配置（如为文档类 PR 跳过 appstore 检查，或在路径白名单中增加根级 README 文件），而非修改 README 文件内容。`pr.changed_files` 限制仅允许修改 `README.en.md` 和 `README.md`，这两个文件内容正确无需更改。

## 潜在风险
无——未对源代码做任何修改。