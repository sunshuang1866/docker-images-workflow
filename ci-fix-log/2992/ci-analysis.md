# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo mirror

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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在下载多个包（gcc-gfortran、glibc-devel、guile、gcc 等）时持续触发 HTTP/2 流帧层错误（`Curl error (92): INTERNAL_ERROR`），dnf 耗尽所有镜像重试后仍无法完成下载，导致 builder 阶段构建失败，stage-1 阶段随即被 CANCELED。

### 与 PR 变更的关联
PR 变更与本次失败无关。PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 的 dnf install 命令语法和包名均正确。失败完全由 openEuler 24.03-LTS-SP4 仓库服务器端 HTTP/2 协议异常导致，属于 CI 基础设施/上游仓库问题。

关键观察：
- dnf 仓库元数据（repomd）下载阶段全部成功（OS、everything、EPOL、debuginfo、source、update、update-source 均正常完成）
- 实际 RPM 包下载阶段出现间歇性 HTTP/2 流错误，且发生在多个不同包上
- builder 阶段（需下载 157 个包）和 stage-1 阶段（需下载 32 个包）并行执行时均受影响，但 stage-1 完成了 23/32 个包的下载后才被 CANCELED，说明错误是非确定性的

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施问题，与 PR 代码无关。建议重新触发 CI 构建（retry），等待上游 openEuler 24.03-LTS-SP4 仓库恢复稳定。若多次重试仍失败，需联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务器配置。

### 方向 2（置信度: 低）
如果仓库持续不稳定，可考虑在 Dockerfile 的 dnf install 命令前添加 `dnf config-manager` 回退到 HTTP/1.1（`--setopt=http2=false`），绕过 HTTP/2 帧层问题。但此方案是临时绕过，非根本修复，不建议作为正式方案提交。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时段是否存在已知的服务中断或降级
2. 重试构建后是否仍然失败——若仍失败则需排查仓库侧问题，若成功则证实为间歇性网络故障
3. 同一仓库的其他 24.03-lts-sp4 Dockerfile（如 PR 中其他 image）在此时间段是否也遇到相同问题——若是则确认系共因仓库故障
4. CI 构建环境是否使用了自定义 dnf 代理或镜像配置，是否存在代理层导致的 HTTP/2 兼容性问题
