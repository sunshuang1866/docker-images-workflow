# 修复摘要

## 修复的问题
本次 CI 失败为 **infra-error**，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 `repo.openeuler.org` 官方软件源在 aarch64 CI runner 构建时段出现间歇性 HTTP/2 连接中断（curl error 92: INTERNAL_ERROR）和 SSL 传输失败（curl error 56: SSL_ERROR_SYSCALL），导致 `vim-common` 包下载失败，进而 `yum install` 步骤以 exit code 1 退出。

该失败与 PR #2977 的代码变更无关。PR 新增的 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 内容语法正确、依赖包声明有效（yum 日志中 173 个依赖包已全部成功解析），纯粹是 openEuler 镜像站瞬时网络波动导致。

**建议操作**：触发 CI 重新构建即可，大概率可直接通过。

## 潜在风险
无