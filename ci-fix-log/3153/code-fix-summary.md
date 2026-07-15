# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），由 `eulerpublisher` 工具的路径校验逻辑 bug 引起，与本次 PR 的 README.md 文档更新完全无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败来自 `eulerpublisher/update/container/app/update.py:273`（CI 发布规范预检步骤），该工具对 `README.md` 执行路径校验时报告"期望路径应为 /README.md"
- 该文件确实位于仓库根目录 `/README.md`，错误与文件实际位置矛盾，属于 CI 工具的路径解析 bug 或 fork 分支克隆环境差异导致
- 本次 PR (#3153) 仅修改了 `README.md` 中"可用镜像的 Tags"段落的文档内容，没有任何 Dockerfile、构建脚本或元数据文件的变更，与 CI 路径校验失败无任何关联
- 报告置信度为"低"，建议由 CI 平台团队修复 `eulerpublisher` 校验逻辑或检查 fork 分支目录结构

根据修复原则，分析报告判定为 `infra-error` 时不应强行修改代码。

## 潜在风险
无。未对源码仓库做任何修改。