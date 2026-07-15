# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（RUN dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库在 CI 构建期间出现 HTTP/2 流传输错误（Curl error 92），3 个包（cmake-data、git-core、gcc-c++）先后遇到此问题。cmake-data 和 git-core 在镜像重试后下载成功，但 gcc-c++（13MB）两次重试均失败，最终 dnf 耗尽所有镜像后构建终止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增了一个 Dockerfile（及配套的 README.md、image-info.yml、meta.yml 条目），Dockerfile 中的 `dnf install` 命令本身语法正确、包名合法。失败纯粹因为 CI 构建环境中访问 openEuler SP4 软件仓库时发生了 HTTP/2 层面的网络传输错误，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**等待并重试构建。** 此问题为 CI 构建环境中 openEuler 24.03-LTS-SP4 仓库镜像的瞬时网络故障（HTTP/2 stream INTERNAL_ERROR），3 个受影响的包中有 2 个已通过镜像重试机制成功下载，仅 gcc-c++ 在耗尽重试后失败。此类网络波动通常是暂时的，重新触发 CI 构建大概率会成功。Code Fixer 无需修改任何代码。

## 需要进一步确认的点
- 如果多次重试构建仍然在相同包上失败（尤其是 gcc-c++），则需排查 openEuler SP4 仓库镜像是否存在持续性的 HTTP/2 配置问题，或考虑在 dnf 配置中禁用 HTTP/2 回退到 HTTP/1.1。
- 如果相同时间点其他 SP4 相关的 PR 也报告了类似的 Curl error (92)，则可确认是仓库端的瞬时故障。
