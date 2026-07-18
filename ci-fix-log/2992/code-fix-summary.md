# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施问题（infra-error），与 PR #2992 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败原因是 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 服务端不稳定，导致 `dnf install` 下载 RPM 包时遭遇 Curl error (92): Stream error in the HTTP/2 framing layer。多个包（gcc、gcc-gfortran、guile 等）在重试过程中耗尽所有镜像后下载失败。

PR 变更仅为新增 Dockerfile 和更新元数据文件，Dockerfile 中的 `dnf install` 命令语法和包名均正确。同一构建中 stage-1 阶段也出现了相同错误但在重试中恢复，说明这是仓库镜像的临时性问题，而非代码问题。

## 潜在风险
无。建议触发 CI 重试（re-run），待 openEuler 24.03-LTS-SP4 软件仓库服务恢复后构建应能通过。