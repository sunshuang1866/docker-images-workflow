# 修复摘要

## 修复的问题
无需代码修改——该失败为 openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 流错误导致的 CI 基础设施瞬态故障（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出失败类型为 **infra-error**，根因是 openEuler 24.03-LTS-SP4 软件仓库镜像服务器在处理 HTTP/2 连接时发生内部流错误（`INTERNAL_ERROR (err 2)`），导致 dnf 下载 `gcc-c++` 等 RPM 包时连接被异常关闭。PR 新增的 Dockerfile 语法正确、`dnf install` 命令格式无问题，与 PR 变更无直接关联。该错误属于偶发性网络故障，具有自愈特性，重试 CI 构建即可通过。

## 潜在风险
无