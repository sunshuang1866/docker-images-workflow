# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像站（`repo.****.org`）存在 HTTP/2 协议稳定性问题，多个 RPM 包的下载流被中断（`Curl error (92): INTERNAL_ERROR (err 2)`）。builder 阶段需下载 157 个包（总计 261 MB），其中 `gcc`（34 MB）和 `gcc-gfortran`（13 MB）等大包多次重试均失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试次数后下载失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）及配套的元数据和文档条目。Dockerfile 本身的语法、包名、版本号均正确——日志显示 `dnf` 成功解析了依赖关系（`Dependencies resolved.`）、列出了完整的包清单（157 个包），问题出在后续的包下载阶段。两个并行的 Docker 构建阶段（`#7` stage-1 和 `#8` builder）同时遭遇 HTTP/2 流中断错误，进一步确认这是镜像站端的网络基础设施问题，而非 Dockerfile 配置错误。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题（openEuler 24.03-LTS-SP4 镜像站 HTTP/2 协议不稳定），无需修改 PR 代码。重新触发 CI 构建（retry）即可——镜像站的网络问题通常是瞬时的，在同一时间段内两个并行构建阶段都受影响，但稍后重试大概率恢复正常。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 官方镜像站）在 CI 构建时段是否存在已知的 HTTP/2 服务端问题或维护窗口。
- 如果在多次 retry 后仍然失败，需要检查是否是该镜像站对 CI 构建环境的 IP 或并发连接数存在限制（如 rate limit 触发 `INTERNAL_ERROR`）。
- 确认 CI 构建节点的网络出口是否对 HTTP/2 长连接下载大文件存在稳定性问题（如中间代理或防火墙干扰 HTTP/2 帧）。
