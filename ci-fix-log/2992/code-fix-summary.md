# 修复摘要

## 修复的问题
此 CI 失败为 **infra-error**（基础设施问题），无需代码修改。

## 修改的文件
无（基础设施错误，不需要修改任何源码文件）

## 修复逻辑
CI 构建失败的直接原因是 openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）在构建期间出现 HTTP/2 传输层错误（Curl error 92: Stream error in the HTTP/2 framing layer），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败，DNF 重试全部镜像后报错退出。

该失败与 PR #2992 的代码变更无关。PR 仅新增了标准 Dockerfile，其 `dnf install` 命令语法完全正确。runtime 阶段同样遭遇了同类 Curl error (92)，进一步印证这是远端仓库的系统性问题。

**建议操作**：重新触发 CI 构建（retry），等待 openEuler 24.03-LTS-SP4 仓库恢复连接稳定性。若多次重试仍失败，需联系 openEuler 镜像站运维排查仓库侧 HTTP/2 服务配置。

## 潜在风险
无