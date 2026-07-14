# 修复摘要

## 修复的问题
无需修改任何代码。CI 失败由 openEuler 24.03-LTS-SP4 软件源镜像服务器的 HTTP/2 传输层故障（Curl error 92: INTERNAL_ERROR）导致，属于 CI 基础设施问题（infra-error）。

## 修改的文件
无代码修改。

## 修复逻辑
失败根因是 openEuler 软件源镜像服务器在 HTTP/2 传输层发生流错误，导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包下载失败，dnf 耗尽所有可用镜像后报错退出。Dockerfile 中 `dnf install` 命令的语法和包名完全正确，与 PR 代码变更无关。

此为临时基础设施故障，无需对 PR 涉及的任何文件进行修改。待镜像源恢复后重新触发 CI 构建即可。

## 潜在风险
无