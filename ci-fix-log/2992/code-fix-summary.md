# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 **infra-error**（基础设施问题），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败根因为 openEuler 24.03-LTS-SP4 RPM 仓库镜像在通过 HTTP/2 协议传输大型软件包（gcc、gcc-gfortran、guile 等）时反复出现 `Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，导致 DNF 重试所有镜像后仍无法下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`。

PR 新增的 Dockerfile 语法和使用方式均正确，与历史 `cb37c53-oe2403sp3` 版本的 Dockerfile 模式一致。失败原因与 PR 代码无关，属于 openEuler 仓库镜像侧的临时网络/协议故障。

**建议操作**：重新触发 CI 构建，有很大概率在仓库镜像恢复后通过。

## 潜在风险
无