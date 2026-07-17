# 修复摘要

## 修复的问题
CI 失败为基础设施问题（infra-error），无需代码修改。失败原因为 openEuler 24.03-LTS-SP4 上游软件仓库 HTTP/2 传输层流中断，导致 `gcc-c++` 等 RPM 包下载失败。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确判定为 `infra-error`，置信度高。失败根因为 openEuler 24.03-LTS-SP4 仓库服务器端 HTTP/2 协议实现缺陷（`INTERNAL_ERROR (err 2)`），与 PR #2980 的代码变更无关。Dockerfile 中 `dnf install` 的包列表语法正确，所有包名均为仓库中真实存在的包。

该问题属于上游仓库服务器的瞬时网络故障，代码层面无需任何修改。重新触发 CI 构建即可通过。

## 潜在风险
无