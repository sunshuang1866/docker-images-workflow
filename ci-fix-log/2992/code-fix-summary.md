# 修复摘要

## 修复的问题
CI 构建失败由 openEuler 24.03-LTS-SP4 RPM 仓库镜像的临时 HTTP/2 协议层不稳定导致，属于基础设施问题（infra-error），与 PR 代码变更无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 日志显示多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）在下载时遇到 `Curl error (92): Stream error in the HTTP/2 framing layer` 错误，这是 openEuler 官方仓库镜像 `repo.****.org` 在构建期间的临时性 HTTP/2 协议层面故障。Dockerfile 中 `dnf install` 的命令语法正确，与同项目其他版本结构一致。PR 仅新增了 24.03-LTS-SP4 的构建配置及元数据，无代码缺陷。建议在仓库镜像恢复稳定后重新触发 CI。

## 潜在风险
无