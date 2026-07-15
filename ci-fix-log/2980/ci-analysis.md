# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2协议错误
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

#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 镜像仓库（`repo.****.org`）在 HTTP/2 传输层持续出现 `INTERNAL_ERROR`（Curl error 92），导致多个 RPM 包下载中断。其中 `cmake-data` 和 `git-core` 在 dnf 后续重试轮次中成功下载，但 `gcc-c++`（13MB）在经历 2 次 HTTP/2 流错误后耗尽了所有镜像重试次数，最终 dnf 报告 `No more mirrors to try`，整个 `dnf install` 步骤失败。

### 与 PR 变更的关联
**与 PR 代码无关。** PR 仅新增了一个标准的 Dockerfile，其 `dnf install` 步骤中声明的所有包名均在 openEuler 24.03-LTS-SP4 仓库中存在（从日志中的 `Dependencies resolved` 列表可以确认全部 258 个包均被 dnf 成功识别并解析了依赖关系）。失败纯粹是由于目标镜像仓库的 HTTP/2 基础设施不稳定，导致大文件（如 13MB 的 `gcc-c++`）下载在多个流传输中反复被中断。这是一个 CI 基础设施层面的瞬时网络故障，与 PR 的代码变更无因果关联。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 构建。** 该失败属于 openEuler 24.03-LTS-SP4 RPM 仓库的瞬时 HTTP/2 传输故障，与 PR 代码完全无关。直接重新触发 CI Job 即可，大多数情况下仓库会在短时间内恢复正常。无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 中）
如果多次重试均因相同包的 HTTP/2 错误失败，则可能是该特定大文件（`gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`）在镜像服务器端的缓存或传输层面存在问题。此时可尝试在 CI 环境或 Dockerfile 中通过 `dnf install` 之前设置环境变量 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 回退到 HTTP/1.1，绕过 HTTP/2 流层问题。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `repo.****.org` 镜像仓库当前是否已恢复正常，可通过在环境中单独执行 `dnf download gcc-c++ --releasever=24.03-lts-sp4` 验证。
- 如果同一仓库近期有其他 openEuler 24.03-LTS-SP4 镜像构建成功，可佐证本次为瞬时故障。
- 若该仓库持续出现 HTTP/2 错误，需联系 openEuler 基础设施团队排查 `repo.****.org` 的反向代理或 CDN 层 HTTP/2 配置问题。
