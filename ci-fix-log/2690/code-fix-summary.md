# 修复摘要

## 修复的问题
PR #2690 新增 kuberay 镜像时遗漏了 appstore 发布规范要求的 LOGO 文件 `Cloud/kuberay/doc/picture/logo.png`，导致 CI lint 预检阶段失败。

## 修改的文件
- `Cloud/kuberay/doc/picture/logo.png`: 新增 kuberay LOGO 图片文件（Ray 项目 GitHub avatar，460x460 PNG），满足 appstore 发布规范的 LOGO 检查项。

## 修复逻辑
CI 分析报告指出 `Cloud/kuberay/doc/picture/logo.*` 缺失，触发 appstore 发布规范预检失败。对照项目规范 CLAUDE.md 第 4 条 Logo Policy（优先使用官方 GitHub avatar）以及第 9 条 Minimal Change Set（doc/picture/logo.png 为必需文件），从 `avatars.githubusercontent.com/ray-project` 获取 Ray 项目官方 avatar 作为 kuberay 的 LOGO。此来源与 `run_workflow.py:143-145` 中 logo 回退逻辑一致（`upstream.version_url: ray-project/kuberay`）。

## 潜在风险
无。仅新增一个必需的 PNG 资源文件，不影响其他功能。