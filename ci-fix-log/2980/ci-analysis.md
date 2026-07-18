# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在通过 DNF 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），gcc-c++ 在重试所有镜像后仍失败，导致整个 `dnf install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的 Dockerfile 内容正确——DNF 依赖解析阶段成功完成了 258 个软件包的事务规划，说明所有列出的包名均存在于仓库中，仓库元数据访问无问题。失败仅因实际下载 RPM 文件时，openEuler 仓库服务器端发生 HTTP/2 传输异常（`stream was not closed cleanly: INTERNAL_ERROR`），属于基础设施层的瞬时网络故障，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 该失败为 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务端瞬时故障，与 Dockerfile 内容无关。直接重新触发 CI 构建（re-run），在网络状况正常时应当能通过。若多次重试均因相同仓库问题失败，需联系 openEuler 基础设施团队排查仓库侧 HTTP/2 服务稳定性。

## 需要进一步确认的点
1. 该仓库镜像 `repo.****.org` 的 HTTP/2 服务端是否存在已知稳定性问题，是否需要从 openEuler 基础设施团队获取确认。
2. 同一时间段内是否有其他 PR 也因 openEuler 24.03-LTS-SP4 仓库下载失败而构建失败，以判断是否为系统性仓库故障。
3. 若重试后仍然失败，需排查是否需要将 DNF 的 HTTP/2 协议降级为 HTTP/1.1（通过设置 `http2=false` 在 `/etc/dnf/dnf.conf` 中），或更换仓库镜像源。

## 修复验证要求
无需额外验证。此为 infra-error，不涉及代码修复。Code Fixer 无需处理。
