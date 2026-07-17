# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，由 openEuler 24.03-LTS-SP4 官方软件仓库的 HTTP/2 服务端流层错误（Curl error 92: INTERNAL_ERROR）导致，与 PR 代码变更无关。

## 修改的文件
无。本次未修改任何代码文件。

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`：
- 失败发生在 `dnf install` 下载 RPM 包阶段，多次出现 `Curl error (92): Stream error in the HTTP/2 framing layer` 和 `INTERNAL_ERROR (err 2)`
- 错误影响多个不同 RPM 包（gcc-gfortran、glibc-devel、guile、gcc），排除单包或单次请求偶发问题
- 错误同时影响 builder 阶段（#8）和 stage-1 最终阶段（#7），属于仓库服务器端或中间代理的 HTTP/2 协议实现缺陷
- Dockerfile 中的 `dnf install` 命令语法和包名均正确，与已有 sp3 版本 Dockerfile 结构一致
- sp3 版本同类 Dockerfile 构建正常，证明问题出在 sp4 仓库侧

**修复方式：等待仓库恢复后重试。** 这是 openEuler 24.03-LTS-SP4 官方软件仓库的临时故障，无需修改代码，等待仓库运维方修复后重新触发 CI 构建即可。若问题持续，可考虑在 Dockerfile 中降级 curl 连接协议（方向 2），但此非本次修复范围。

## 潜在风险
无。未做任何代码修改，无引入新问题的风险。