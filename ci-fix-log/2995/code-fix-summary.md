# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无。PR 涉及的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均正确无误，Docker 镜像构建全程成功。

## 修复逻辑
CI 失败发生在 [Check] 阶段，`eulerpublisher` 包自带的测试脚本 `bwa_test.sh` 包含 Windows 风格的行尾符（CRLF），导致 shebang 行 `/bin/sh` 被 Shell 解析为 `/bin/sh^M`，系统无法找到解释器。该脚本位于 CI 基础设施的 `eulerpublisher` RPM 包中，不在本仓库范围内。

修复需由 CI 基础设施维护者在 `eulerpublisher` 仓库中对该测试脚本执行 `dos2unix` 或通过 `.gitattributes` 强制 LF 换行符，重新发布 RPM 包后重新触发 CI 即可验证。

## 潜在风险
无。本仓库无任何代码变更。