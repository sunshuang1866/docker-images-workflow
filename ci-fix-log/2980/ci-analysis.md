# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，HTTP/2 协议层出现多次流错误（`Curl error (92)`），导致三个包（cmake-data、git-core、gcc-c++）下载过程中断并触发重试。其中 cmake-data 和 git-core 在重试后成功下载，但 gcc-c++（13 MB）经过多次重试后所有镜像均失败，dnf 无更多镜像可尝试，整个 `dnf install` 命令退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及相关元数据文件，Dockerfile 中的 `dnf install` 命令语法和包名均正确。失败根因是 CI 基础设施网络层问题——openEuler RPM 仓库的 HTTP/2 传输层发生了 `INTERNAL_ERROR`，属于服务器端或网络中间件的临时故障，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此次失败是 openEuler 仓库网络传输的临时性故障（HTTP/2 stream INTERNAL_ERROR），属于 infra-error，无需修改任何代码。在 CI 上重新触发该 job 即可（网络状况正常时通常能成功）。

### 方向 2（置信度: 低）
**若重试多次仍失败，考虑在 Dockerfile 的 dnf 命令中添加重试机制或切换镜像源。** 如果 openEuler 仓库持续出现 HTTP/2 协议问题（可能性极低），可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加重试次数，或配置备用 yum 镜像源。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 RPM 仓库在当前时间的网络可达性和 HTTP/2 协议健康状况。如果多次重试 CI 后问题依然存在，需要联系 openEuler 基础设施团队排查 repo 服务器的 HTTP/2 配置或上游代理。
