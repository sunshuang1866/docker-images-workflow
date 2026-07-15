# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 仓库镜像站下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），`gcc-c++` 在重试多次后仍然失败，最终 `dnf` 因"所有镜像均已尝试但无一成功"而退出，导致 Docker 镜像构建在包安装阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个语法正确、依赖声明完整的 Dockerfile（以及配套的 README.md、image-info.yml、meta.yml 元数据更新）。所有变更均为纯文本/配置类添加，不涉及任何可能导致网络错误的代码逻辑。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 协议层间歇性故障，属于 CI 基础设施问题。部分包（如 `gcc` 34MB、`git-core` 11MB）在经历 HTTP/2 错误后通过重试成功下载，进一步说明这是网络层面的瞬时不稳定。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 构建即可。** 此失败为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 仓库镜像站在构建期间出现 HTTP/2 协议层间歇性故障。在镜像站恢复正常后，重新触发 CI 构建（trigger by note）应能成功通过。若重试仍失败，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 参数以提高对网络波动的容忍度（但这不是根本解决方案）。

## 需要进一步确认的点
1. 在重试 CI 前，确认 openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org/openEuler-24.03-LTS-SP4`）当前是否可从 CI runner 所在网络正常访问且稳定。
2. 若重试多次（≥3 次）后仍反复出现同样的 HTTP/2 流错误，需联系镜像站运维排查 HTTP/2 协议层配置是否存在问题。

## 修复验证要求
无需验证（infra-error，与代码变更无关，重试 CI 即可）。
