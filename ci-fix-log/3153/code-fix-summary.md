# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施误报（infra-error），PR #3153 仅修改了根目录文档文件 `README.md` 和 `README.en.md`，不应触发 appstore 发布规范检查。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定此次失败为 infra-error：
- 失败来源是 CI 工具 `eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑，它将根目录的 `README.md` 误判为不符合 `/README.md` 预期路径格式（路径归一化缺陷）。
- PR 仅修改了 `README.md`（更新可用基础镜像 tags 列表），属于纯文档维护性变更，不涉及任何 Dockerfile、meta.yml 等应用镜像构建文件，本不应触发 appstore 发布规范检查。
- 此问题需要 CI 维护方调整校验规则（排除纯文档 PR 或修复路径归一化逻辑），无需对源码仓库代码做任何修改。

## 潜在风险
无