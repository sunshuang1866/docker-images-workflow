# 修复摘要

## 修复的问题
无需代码修改 — 本次 CI 失败为 `infra-error`。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 `repo.openeuler.org` 在 aarch64 runner 上构建时出现网络不稳定，导致 yum 在下载 `vim-common` 等 RPM 包时发生多次 Curl 错误（HTTP/2 流异常中断、SSL 读取失败），yum 重试耗尽后报错退出。PR #2977 新增的 Dockerfile 内容与已有 SP3 版本结构一致，包依赖声明正确，与网络故障无关。此问题属于 CI 基础设施侧临时性网络波动，重新触发 CI 构建大概率可成功通过，无需对 PR 代码做任何修改。

## 潜在风险
无