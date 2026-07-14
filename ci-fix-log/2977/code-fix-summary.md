# 修复摘要

## 修复的问题
CI 基础设施故障：`repo.openeuler.org` 对 aarch64 构建节点的网络服务不稳定，导致 `yum install` 下载 RPM 包时出现 Curl error (92) HTTP/2 流错误和 Curl error (56) SSL 连接中断，最终 `vim-common` 包在所有镜像源重试耗尽后下载失败。

## 修改的文件
无

## 修复逻辑
本次 CI 失败属于 **infra-error**（CI 基础设施问题），与 PR 代码变更无关。该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件，Dockerfile 语法正确、依赖声明合理。失败根因是 openEuler 官方软件仓库 `repo.openeuler.org` 的网络服务瞬态故障。

**无需修改代码**，在仓库网络恢复后重新触发 CI 构建即可通过。

## 潜在风险
无