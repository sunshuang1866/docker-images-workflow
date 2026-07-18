# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：CI runner 上缺少 `shunit2` Shell 测试框架，导致 eulerpublisher 的 `[Check]` 阶段无法执行容器镜像验证测试。**与 PR 代码变更无关，无需修改任何 PR 代码。**

## 修改的文件
无。此次为 CI 基础设施问题，PR 本身的 Dockerfile、named.conf、meta.yml、image-info.yml 及 README.md 变更均正确无误，Docker 镜像构建全部成功。

## 修复逻辑
CI 分析报告明确指出根因是 `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh:13` 引用的 `shunit2` 文件在 CI runner 上不存在。Docker 镜像构建阶段（meson compile 422/422 全部通过，所有库文件和二进制均正确安装，镜像推送也成功完成）完全正常，失败仅发生在 CI 基础设施的 `[Check]` 后处理阶段。

修复方案：需要在执行容器镜像检查的 CI runner 上安装 `shunit2` Shell 测试框架（kward/shunit2），确保该脚本被放置在 CI runner 的 `PATH` 中或 `common_funs.sh` 能引用的路径下。此工作属于 CI 运维侧，不属于源代码修改范围。

## 潜在风险
无。本次不涉及任何源代码修改。