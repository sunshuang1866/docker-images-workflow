# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error，根因是 eulerpublisher CI 测试基础设施中内置的 `bwa_test.sh` 脚本包含 Windows 风格换行符（CRLF），导致 shebang 被解析为 `/bin/sh^M`，与本次 PR 的代码变更无关。

## 修改的文件
无（infra-error，PR 涉及的文件均无需修改）

## 修复逻辑
本次 PR 新增的 bwa 0.7.18 openEuler 24.03-LTS-SP4 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）均正确无误。Docker 镜像构建阶段已完全成功（源码下载、gcc 编译、镜像推送均正常完成）。CI 失败发生在构建完成后的 [Check] 阶段，由 eulerpublisher 包内置测试脚本的 CRLF 换行符问题导致，需要 eulerpublisher 维护者在其源码仓库中将 `tests/container/app/bwa_test.sh` 的行尾序列从 CRLF 转换为 LF 后重新发布包。PR 作者侧无需也无法修改此基础设施问题。

## 潜在风险
无