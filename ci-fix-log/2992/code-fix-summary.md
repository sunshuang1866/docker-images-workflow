# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确指出，失败类型为 **infra-error**，根因是 openEuler 24.03-LTS-SP4 软件仓库源（`repo.****.org`）在 HTTP/2 协议层面存在服务端不稳定问题，导致 `dnf install` 下载多个 RPM 包时反复出现 Curl error (92): Stream error in the HTTP/2 framing layer。

该 PR 仅新增了面向 openEuler 24.03-LTS-SP4 的 Dockerfile，其中 `dnf install` 安装的均为标准仓库包（git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel），包名和版本均正确无误，与 PR 代码变更无关。

应在 CI 基础设施层面处理：
- 等待仓库源恢复后重新触发 CI；
- 或在 CI 的 dnf 配置中禁用 HTTP/2 回退到 HTTP/1.1；
- 或切换到备用镜像源。

## 潜在风险
无。未修改任何代码，不会引入新问题。