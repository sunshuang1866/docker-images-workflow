# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ... git && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 镜像仓库（`repo.****.org`）在 CI 构建期间频繁出现 HTTP/2 流协议错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包下载中断。gcc-c++ 包经过多次重试后所有镜像源均告失败，最终 `dnf install` 以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（及配套的 README.md、image-info.yml、meta.yml 文档/元数据更新）。Dockerfile 中的 `dnf install` 命令和包列表语法正确，错误完全发生在从远程仓库下载 RPM 包的阶段，属于 CI 构建环境与 openEuler 仓库之间的网络/协议层基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该失败为 CI 基础设施层面的瞬态故障——openEuler 24.03-LTS-SP4 的 RPM 仓库在某些时段出现 HTTP/2 流协议不稳定。无需修改任何代码或 Dockerfile，触发一次 re-run / retry 即可大概率通过。若多次重试仍失败，需排查 CI 构建节点到 `repo.****.org` 之间的网络链路或仓库端 HTTP/2 服务状态。

### 方向 2（置信度: 低）
**降级到 HTTP/1.1。** 若 HTTP/2 问题持续且确认是仓库端的长期问题，可在 Dockerfile 的 `dnf install` 前通过设置 DNF/Curl 配置禁用 HTTP/2（如 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `curl` 相关环境变量），临时绕过 HTTP/2 协议层故障。但此为短期 workaround，不建议作为永久方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 的 HTTP/2 服务状态是否稳定（可尝试从其他节点 `curl --http2` 下载同一 RPM 验证）。
- CI 构建节点 `ecs-build-docker-x86-03-sp` 到该仓库的网络链路质量（是否存在代理/防火墙干扰 HTTP/2 长连接）。
