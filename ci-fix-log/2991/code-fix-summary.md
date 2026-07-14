# 修复摘要

## 修复的问题
CI 构建失败为基础设施网络错误（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败由 `repo.openeuler.org` 仓库服务器在处理 HTTP/2 请求时出现瞬时流错误（Curl error 92: `INTERNAL_ERROR (err 2)`）导致，多个不同 RPM 包（`git-core`、`gcc-c++`、`guile`）下载时均遇到相同错误，排除了特定包损坏的可能性。PR 代码（Dockerfile 及元数据文件）无缺陷，`dnf install` 命令格式正确，与同仓库其他 24.03-lts-sp4 镜像写法一致。建议重新触发 CI 构建即可。

## 潜在风险
无