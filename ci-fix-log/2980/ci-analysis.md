# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Repo镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, INTERNAL_ERROR (err 2), dnf, repo

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 连接不稳定，dnf 在下载 258 个包时，多个包（cmake-data、git-core、gcc-c++）先后遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`。cmake-data 和 git-core 在重试后下载成功，但 gcc-c++（13 MB 的大包）两次重试均失败，dnf 耗尽所有镜像后构建失败。

### 与 PR 变更的关联
**与 PR 代码无关**。该 PR 仅新增了一个标准格式的 Dockerfile（安装依赖 → 克隆源码 → 编译安装），Dockerfile 中的 `dnf install` 命令本身没有问题。失败完全由 openEuler SP4 软件仓库镜像的 HTTP/2 协议层不稳定导致，属于基础设施层面的间歇性故障。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。ERROR 是 HTTP/2 流层间歇性中断（`INTERNAL_ERROR (err 2)`），并非仓库中不存在软件包。日志显示 cmake-data 和 git-core 在重试后均成功下载，仅 gcc-c++ 在两次重试后未恢复。等待仓库镜像恢复稳定后重试，构建大概率可以成功。

### 方向 2（置信度: 低）
**在 Dockerfile 中配置 dnf 禁用 HTTP/2**。如果 openEuler SP4 仓库镜像持续存在 HTTP/2 兼容性问题，可在 `dnf install` 前通过 dnf.conf 或 curl 配置强制使用 HTTP/1.1（设置 `http2=false` 或 `max_parallel_downloads=1`），绕过 HTTP/2 流层错误。但目前仅有单次失败记录，不足以判断是否为持续性基础设施问题，此方向仅为备选。

## 需要进一步确认的点
1. 该 CI 失败是否为可复现的稳定失败，还是偶发性网络波动？需要重试构建至少 1-2 次来确认。
2. 如果多次重试均以相同错误失败，则需要确认 `repo.openeuler.org` 对 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端配置是否存在已知问题。
3. 同一个 CI runner（`ecs-build-docker-x86-03-sp`）上其他 SP4 镜像的构建是否也遭遇了同样的 HTTP/2 错误？如果其他镜像也失败，则进一步佐证是仓库基础设施问题。

## 修复验证要求
无需特殊验证。若采用方向 1（重试构建），只需等待 CI 重新运行即可。若采用方向 2（禁用 HTTP/2），需验证修改后的 Dockerfile 在 CI 环境中能成功通过 `dnf install` 步骤。
