# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder stage 的 `dnf install` 步骤）
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）均遭遇 HTTP/2 协议层 Stream Error（Curl error 92: Stream error in the HTTP/2 framing layer, INTERNAL_ERROR），在重试所有可用镜像后仍全部失败，最终 gcc 包报 "No more mirrors to try"，`dnf install` 以 exit code 1 失败。build 阶段（#8）失败后，runtime 阶段（#7）被自动取消（CANCELED）。

### 与 PR 变更的关联

**与 PR 变更无关。** 该 PR 仅新增了 Multiwfn 的 SP4 Dockerfile 及配套的 README、meta.yml、image-info.yml 条目，Dockerfile 内容本身语法正确、结构合理（与已有的 SP3 版本一致）。失败的直接原因是 openEuler 24.03-LTS-SP4 仓库镜像服务的 HTTP/2 连接在 CI 构建期间不稳定，属于 CI 基础设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试即可。** 该失败为 CI 基础设施临时性故障——openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 层出现间歇性 Stream 中断。Code Fixer 无需修改任何代码，只需触发 CI 重新构建（rerun）。若重试后仍持续失败，则需联系 infra/运维团队排查 openEuler SP4 仓库镜像服务的 HTTP/2 配置或网络状况。

### 方向 2（置信度: 低，仅当重试多次仍持续失败时考虑）
**换源绕过。** 若 SP4 仓库镜像的 HTTP/2 问题长期存在且无法修复，可在 Dockerfile 的 `dnf install` 前通过配置 `dnf` 使用 HTTP/1.1 协议或换用其他 SP4 镜像源。但这属于临时 workaround，不应作为首选方案。

## 需要进一步确认的点

- 检查同时间段其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 构建是否也整体失败——若多 PR 同时出现相同错误，进一步确认是 SP4 仓库镜像服务端问题。
- 检查 x86-64 runner 到 SP4 仓库镜像的网络连通性及 HTTP/2 会话稳定性。

## 修复验证要求

无需验证——此为 infa-error，重试 CI 即可。若重试后构建仍然失败，再考虑方向 2 并做进一步诊断。
