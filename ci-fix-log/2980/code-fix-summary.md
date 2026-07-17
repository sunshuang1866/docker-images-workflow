# 修复摘要

## 修复的问题
CI 基础设施故障（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 流错误），与 PR 代码无关，无需代码修改。

## 修改的文件
无。此失败为 `infra-error`，不需要修改任何源代码。

## 修复逻辑
CI 构建在 `dnf install` 下载系统软件包时，openEuler 官方仓库镜像 `repo.***.org` 出现 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR），导致 gcc-c++、git-core、cmake-data 等大文件包下载失败。258 个包中有 255 个下载成功，仅个别大文件受间歇性网络故障影响。这是临时性的基础设施/仓库镜像侧问题，与 PR #2980 新增的 Dockerfile 及元数据文件无关。等待仓库镜像恢复后重新触发 CI 构建即可通过。

## 潜在风险
无