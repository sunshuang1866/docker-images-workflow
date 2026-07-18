# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施误检（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 失败由 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检工具触发。该工具扫描到 PR 修改了仓库根目录的 `README.md` 后，将其误判为应用镜像的 README 并执行路径合规性校验，导致校验失败。

PR #3153 仅更新了根 `README.md`（及 `README.en.md`）中的基础镜像 Tags 列表，属于仓库级文档变更，不涉及任何应用镜像的 Dockerfile、meta.yml、image-list.yml 或 image-info.yml。根 `README.md` 本不应受 appstore 路径规则约束。

根据分析报告诊断结果，此问题的修复方向在 CI 工具侧（`update.py`），需在文件扫描逻辑中将根层级 `README.md` / `README.en.md` 加入跳过列表，而非在本仓库代码中修改。因此无需对本仓库任何文件做代码变更。

## 潜在风险
无 — 本仓库未做任何代码修改。