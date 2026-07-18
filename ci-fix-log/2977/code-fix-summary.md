# 修复摘要

## 修复的问题
CI 失败属于基础设施问题（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4` 的 `RUN yum install -y ...` 步骤中。aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 RPM 依赖包时，多个包遭遇 HTTP/2 协议层流传输错误（`Curl error (92): INTERNAL_ERROR`）和 SSL 连接中断（`Curl error (56): SSL_ERROR_SYSCALL`），最终 `vim-common` 包耗尽所有镜像源重试后彻底失败，导致 yum install 退出码为 1。

此失败与 PR #2977 的代码变更（新增 brpc Dockerfile 及元数据文件）完全无关。Dockerfile 中的 `yum install` 命令语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中的标准包。根因是 `repo.openeuler.org` 在 aarch64 通道上的瞬时网络传输问题。

建议：等待 `repo.openeuler.org` aarch64 通道网络状况恢复后，重新触发 CI 构建。

## 潜在风险
无