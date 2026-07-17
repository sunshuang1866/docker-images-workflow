# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 的 RPM 镜像仓库（`repo.****.org`）在 HTTP/2 传输层频繁出现流中断错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++` 等多个包下载失败。其中 `cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++` 重试两次（stream 65、stream 83）后耗尽所有镜像源，`dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个合法的 Dockerfile（包含标准 `dnf install` 命令）及配套元数据文件（README.md、image-info.yml、meta.yml）。`dnf install` 所请求的 258 个包名和依赖关系均被 DNF 正确解析（"Dependencies resolved"），失败纯粹发生在 RPM 包的网络下载阶段，属于构建基础设施/镜像仓库的网络稳定性问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 openEuler 镜像仓库的瞬时网络/HTTP/2 连接不稳定导致，是典型的 `infra-error`。`gcc-c++` 包本身在仓库中存在（DNF 已解析其元数据），只是下载过程中 HTTP/2 流异常中断。此类问题通常会随时间自行恢复，重新运行 CI Job 大概率通过。Code Fixer 无需修改任何代码。

## 需要进一步确认的点
- 无。日志证据充分，错误类型明确为网络基础设施问题。若多次重试 CI 后仍然失败，则需要联系 openEuler 镜像仓库运维排查 HTTP/2 服务端配置或 CDN 节点健康状态。
