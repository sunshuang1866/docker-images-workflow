# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施问题——openEuler 24.03-LTS-SP4 RPM 仓库镜像在本次 CI 运行期间出现 HTTP/2 协议层连接异常（Curl error 92: INTERNAL_ERROR），导致 `gcc`、`gcc-gfortran`、`guile` 等软件包下载失败，所有镜像被尝试后均失败，`dnf install` 步骤退出码为 1。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
失败根因是 openEuler 仓库镜像的暂时性网络波动（HTTP/2 协议层连接异常），与 PR #2992 的代码变更无关。Dockerfile 中的 `RUN dnf install` 命令语法正确，依赖声明无误。重新触发 CI 流水线（retry/re-run）即可。若重试多次仍失败，需联系 openEuler 镜像站运维确认 24.03-LTS-SP4 仓库的 HTTP/2 服务状态。

## 潜在风险
无（无代码改动）