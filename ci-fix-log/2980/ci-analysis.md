# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在处理 HTTP/2 下载请求时多次出现流错误（`INTERNAL_ERROR (err 2)`），导致三个软件包（cmake-data、git-core、gcc-c++）的下载均受到不同程度的影响。其中 cmake-data 和 git-core 在重试后成功，但 gcc-c++ 两次尝试均失败，最终 dnf 耗尽所有镜像后报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 中 `dnf install` 命令语法完全正确，所列软件包名称均为 openEuler 24.03-LTS-SP4 仓库中实际存在的有效包（日志中 `Dependencies resolved` 阶段已成功解析全部 258 个包的依赖关系并开始下载）。失败纯粹由 openEuler 镜像仓库服务器的 HTTP/2 传输层间歇性故障导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为镜像仓库服务器的瞬时 HTTP/2 传输层故障，属于 `infra-error`，与 PR 代码变更无关。大多数情况下重试即可通过。Code Fixer 无需对 Dockerfile 做任何修改。

## 需要进一步确认的点
无。日志证据充分：依赖解析成功（258 个包），下载过程因仓库服务器的 HTTP/2 流错误而中断，多个包受影响但最终仅有 gcc-c++ 彻底失败。所有证据指向上游镜像仓库的瞬时基础设施问题。
