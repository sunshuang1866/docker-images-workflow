# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`，由 openEuler 官方软件仓库 `repo.openeuler.org` 的 HTTP/2 协议间歇性故障（Curl error 92）导致 `dnf install` 步骤下载 RPM 包失败，与 PR 代码无关。

## 修改的文件
无。所有 PR 变更文件（`Dockerfile`、`README.md`、`image-info.yml`、`meta.yml`）内容正确，无需修改。

## 修复逻辑
分析报告判定失败类型为 `infra-error`，根因不在代码层面。`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` 的 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令与已有 `sp3` 版本 Dockerfile 中的同类命令完全一致，属于标准的系统包安装操作。失败由远程镜像站 HTTP/2 stream INTERNAL_ERROR 引起，仅需重新触发 CI 构建。

## 潜在风险
无。若问题频繁出现，建议 CI 运维团队排查 openEuler 镜像站 HTTP/2 稳定性，或为 dnf 配置回退镜像源/增加重试次数。