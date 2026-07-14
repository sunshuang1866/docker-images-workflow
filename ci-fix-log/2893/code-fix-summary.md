# 修复摘要

## 修复的问题
无需代码修改。此次 CI 失败为 `infra-error`：CI runner 环境缺少 `shunit2` shell 测试框架，导致 `[Check]` 阶段在初始化测试脚本时失败。

## 修改的文件
无。Docker 构建（meson setup/compile/install + 镜像导出 & 推送）全部通过，PR 中的 Dockerfile、named.conf 及元数据文件均正确无误。

## 修复逻辑
CI 分析报告明确指出失败发生在 CI runner 的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`，该文件尝试 `source shunit2` 但该框架未安装在 aarch64 runner 上。Docker 构建阶段全部成功，422 个编译目标链接正常，镜像已成功推送。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Docker 镜像，所有 PR 文件无需修改。问题应由 CI 基础设施团队在 runner 节点上安装 `shunit2` 后重新触发 CI。

## 潜在风险
无