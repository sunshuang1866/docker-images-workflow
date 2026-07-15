# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：CI Runner 环境中缺少 `shunit2` shell 测试框架，导致构建完成后的容器校验脚本 (`common_funs.sh`) 无法 source `shunit2`。无需代码修改。

## 修改的文件
无

## 修复逻辑
本次 PR 变更仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关配置文件。CI 日志显示 Docker 镜像构建与推送均已成功完成（422/422 个编译目标全部通过，镜像已推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），失败仅发生在构建完成后的 `[Check]` 测试阶段，即 `eulerpublisher` 的容器启动校验脚本尝试 `source shunit2` 时找不到该文件。

此错误与 PR 代码变更完全无关，属于 CI 基础设施运维问题，需要在 CI Runner 镜像或构建节点上安装 `shunit2` 框架（可通过 `yum install shunit2` 或从 GitHub kward/shunit2 获取部署）。

## 潜在风险
无