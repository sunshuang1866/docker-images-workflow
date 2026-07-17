# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, repo

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库镜像（`repo.****.org`）在 HTTP/2 协议层面出现流中断（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载过程中反复重试后仍失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 因所有镜像源均已尝试无果而彻底失败，dnf 安装命令以 exit code 1 退出，Docker 构建中止。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）语法正确，`dnf install` 命令列出的所有包（git、gcc、gcc-c++、gcc-gfortran、make、openblas-devel、lapack-devel）均为 openEuler 仓库中实际存在的合法包名。失败完全由目标 RPM 仓库的网络/协议层不稳定导致，属于 CI 基础设施层面的临时性问题。即使是没有改动的 stage-1（#7）中相同的 dnf 下载操作也同样出现了 HTTP/2 流错误，进一步证明此问题发生在仓库侧。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试**。此失败为 `repo.****.org` 镜像站的 HTTP/2 协议服务端临时不稳定导致，与代码无关。等待仓库服务恢复后重新触发 CI 流水线即可通过。若多次重试仍失败，可联系 openEuler 镜像站运维团队排查 HTTP/2 协议栈问题。

### 方向 2（置信度: 低）
**更换 dnf 仓库镜像源或禁用 HTTP/2**。如果 `repo.****.org` 的 HTTP/2 问题持续且不可控，可在 Dockerfile 的 `dnf install` 步骤前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 协议下载，规避 HTTP/2 流错误；或将 baseurl 切换为同仓库的其他镜像节点。

## 需要进一步确认的点
- 确认 `repo.****.org` 当前是否处于已知维护或故障状态
- 确认同一时间段其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也出现了相同错误（用于确认故障范围和是否已恢复）
- 如果 aarch64 runner 上也构建了该 Dockerfile，需确认 aarch64 侧的日志是否也有相同问题

## 修复验证要求
无。此失败为 infra-error，不涉及任何代码修复。如需验证方向 2 中的 workaround 方案，在本地或 CI 环境中执行同版本 openEuler 容器的 `dnf install` 命令，确认修改 `dnf.conf` 中的 `http2=false` 后能稳定通过即可。
