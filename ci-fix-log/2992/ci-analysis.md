# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: CI 构建环境从 `repo.****.org`（openEuler 官方仓库）下载 RPM 包时，HTTP/2 连接反复出现 `INTERNAL_ERROR (err 2)` 流错误，多个包（gcc-gfortran、glibc-devel、guile、gcc）均受影响，gcc 包（34 MB）在重试所有镜像后仍未成功下载，dnf 安装失败退出。构建的两个阶段（builder 阶段 157 个包、运行阶段 32 个包）均遭遇同样的 HTTP/2 错误，但 builder 阶段因包数量更多先达到失败阈值。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile 及对应的元数据/文档条目，Dockerfile 本身语法正确、结构合理（与已有的 SP3 Dockerfile 模式一致）。失败根因是 openEuler 24.03-LTS-SP4 官方软件仓库 `repo.****.org` 在 CI 运行时段存在 HTTP/2 层面的网络故障，导致大文件 RPM 包下载不稳定。这是 CI 基础设施侧的瞬态问题，任何依赖该仓库的构建在同一时段都可能失败。

## 修复方向

### 方向 1（置信度: 中）
**等待并重试**。该失败为 `repo.****.org` 仓库服务端 HTTP/2 瞬时故障，与代码无关。建议等待仓库服务恢复后重新触发 CI 构建。若问题持续存在，需联系 openEuler 基础设施团队排查 `repo.****.org` 的 HTTP/2 网关/代理配置。

### 方向 2（置信度: 低）
**切换 dnf 使用 HTTP/1.1**。如果 openEuler 仓库持续存在 HTTP/2 兼容性问题，可考虑在 Dockerfile 的 `dnf install` 前配置 dnf 禁用 HTTP/2（如设置 `http2=false` 或调整 curl/ libcurl 配置），但这不是常规做法，且可能降低下载性能。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库在 CI 失败时段的 HTTP/2 服务状态（是否发生中断/维护）
- 验证同一时段其他依赖 openEuler 24.03-LTS-SP4 仓库的 PR 构建是否也出现相同错误（确认是否为系统性故障）
- 如果重新触发 CI 后仍然失败，需确认是否需要更换镜像源或调整 dnf 仓库配置
