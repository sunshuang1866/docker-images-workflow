# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施错误（infra-error），由 openEuler 官方仓库 `repo.openeuler.org` 的 HTTP/2 服务端间歇性协议错误（INTERNAL_ERROR）导致 aarch64 架构下部分 RPM 包下载失败。

## 修改的文件
无（infra-error，无需修改任何源文件）

## 修复逻辑
根据 CI 失败分析报告，本次失败与 PR #2991 的代码变更无关。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 是标准合法的命令，失败原因是 openEuler 上游仓库服务器在 aarch64 节点上反复出现 HTTP/2 流错误（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`），多个 RPM 包（git-core、gcc-c++、guile）均受影响。部分包经 dnf 自动重试后成功下载，guile 包耗尽了所有镜像重试后失败，最终 `dnf` 以 exit code 1 退出。

**推荐操作**：重新触发 CI 构建。该问题属于临时性基础设施波动，等待上游仓库恢复后重试即可。

## 潜在风险
无