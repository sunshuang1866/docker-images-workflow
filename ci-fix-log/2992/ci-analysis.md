# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, openEuler-24.03-LTS-SP4

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: 构建阶段 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）遇到 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像重试后均失败，导致 dnf 安装步骤以退出码 1 结束。

### 与 PR 变更的关联
PR 仅新增了一个基于 `openeuler/openeuler:24.03-lts-sp4` 的 Dockerfile 及相关元数据文件，Dockerfile 内容本身（`dnf install` 包列表、`make` 命令等）与同项目的 SP3 版本完全一致。失败与 PR 的代码变更**无关**，是 openEuler 24.03-LTS-SP4 软件仓库镜像在 CI 构建时点存在的 HTTP/2 协议异常导致的下载失败。运行时阶段（#7，依赖更少）也同样遭遇了 HTTP/2 流错误（gcc-gfortran stream 15、glibc-devel stream 17），进一步佐证问题出在镜像站而非特定包或 Dockerfile。

## 修复方向

### 方向 1（置信度: 高）
Retry CI 构建。该失败属于临时性基础设施问题（仓库镜像 HTTP/2 服务端异常），非代码引起的确定性错误。在基础设施恢复后重试即可通过。

### 方向 2（置信度: 低）
若多次重试仍失败，可尝试在 Dockerfile 的 `dnf install` 之前添加 `dnf makecache` 并配置重试参数（如 `echo 'retries=10' >> /etc/dnf/dnf.conf`），提高 dnf 对临时网络错误的容忍度。但这属于治标方案，不建议作为永久修复。

## 需要进一步确认的点
- 若重试后仍失败，需检查 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 的服务状态（是否已恢复正常），或确认 CI runner 节点与该镜像站之间的网络连通性。
