# 修复摘要

## 修复的问题
无需代码修复——CI 失败为基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无（未修改任何源代码文件）

## 修复逻辑
CI 失败的根因是 eulerpublisher 包自带的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 测试脚本包含 Windows CRLF 换行符，导致 shebang 解析为 `/bin/sh^M`，内核无法找到该解释器而拒绝执行。

PR 的所有代码变更（Dockerfile、README.md、image-info.yml、meta.yml）均正确无误，Docker 镜像的编译、构建、推送三个阶段全部成功。失败仅发生在 CI 后处理阶段由 eulerpublisher 工具调用基础设施测试脚本时，属于 CI Runner 上 eulerpublisher 包的问题，需 CI 维护者修复，不应修改任何 PR 源码。

## 潜在风险
无