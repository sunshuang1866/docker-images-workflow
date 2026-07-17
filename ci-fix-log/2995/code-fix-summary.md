# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），根因是 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 CRLF 换行符，与 PR 变更无关。

## 修改的文件
无。PR 中的所有文件（Dockerfile、README、image-info.yml、meta.yml）均正确，不需要修改。

## 修复逻辑
CI 失败发生在构建和推送成功之后的 `[Check]` 测试阶段，错误信息为 `/bin/sh^M: bad interpreter: No such file or directory`。根因是 CI 基础设施中 `eulerpublisher` 包自带的 `bwa_test.sh` 脚本使用了 Windows/DOS 风格的 CRLF 换行符，导致 shebang 行末尾携带回车符。PR 的 Dockerfile 及所有变更本身没有引入任何错误，Docker 镜像构建、编译、打包、推送均成功通过。

该问题应由 CI 基础设施维护者修复：在 `eulerpublisher` 包中将 `bwa_test.sh` 转换为 LF 格式（如通过 `dos2unix` 或在 git 中设置 `core.autocrlf`），然后更新 CI runner 上的包版本。

## 潜在风险
无。本次未修改任何代码。