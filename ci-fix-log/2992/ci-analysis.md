# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, repo

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 的官方软件仓库（`repo.****.org`）在构建期间出现 HTTP/2 协议层面的流错误（`Curl error 92: INTERNAL_ERROR`），导致 `gcc` 等大型 RPM 包反复下载失败，最终 dnf 耗尽所有重试 mirror 后报错退出。两个构建阶段（builder #8 和 stage-1 #7）均出现相同的 Curl 92 错误，确认是仓库服务端问题而非单个网络连接波动。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套文档和元数据条目。Dockerfile 内容与已有的 `24.03-lts-sp3` 版本结构一致，语法正确。失败纯粹由 CI 构建时 openEuler 包仓库的 HTTP/2 服务不稳定导致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此为 CI 基础设施故障（openEuler 24.03-LTS-SP4 仓库服务器 HTTP/2 连接不稳定）。建议在仓库服务恢复后重新触发 CI 构建（retry），预期可直接通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org` 或 CI 使用的镜像站）在目标时间段是否存在服务中断或 HTTP/2 协议层面的已知问题。
- 如果多次 retry 后仍出现相同错误，需排查 CI runner 到仓库间的网络链路（防火墙/代理是否干扰 HTTP/2 长连接）。
