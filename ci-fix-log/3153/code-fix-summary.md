# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 appstore 发布规范预检工具对纯文档 PR 缺乏豁免机制引起，属于 CI 基础设施层面的过度校验（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出：PR #3153 仅修改了 `README.md`（更新基础镜像可用 tags 列表），为纯文档维护变更，不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建或元数据文件。失败的直接原因是 `eulerpublisher/update/container/app/update.py:273` 的路径校验规则将仓库根目录的 `README.md` 误判为不符合 appstore 镜像发布规范（`[Path Error]`）。根因不在 PR 代码本身，而在于 CI 预检工具缺少对纯文档 PR 的豁免逻辑。同类历史案例参见模式 11 中的 PR #2512。无需对 `README.md` 或任何源码文件做修改。

## 潜在风险
无