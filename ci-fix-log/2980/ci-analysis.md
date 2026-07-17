# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站在构建期间出现 HTTP/2 协议层流错误（Curl error 92: stream not closed cleanly）。`gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 是唯一耗尽所有重试后下载失败的包，其他受影响的包（`cmake-data`、`git-core`）在重试后成功下载。这是典型的镜像站/网络基础设施瞬时故障，与 PR 代码变更完全无关。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准的 GrADS 2.2.3 Dockerfile（`dnf install` 依赖列表与同类 Dockerfile 一致），以及 README.md、image-info.yml、meta.yml 的对应条目更新。失败发生在 `dnf install` 从 openEuler 官方仓库下载 RPM 包的网络传输阶段，任何在同一时段触发的构建都可能遇到相同问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 该失败为 openEuler 24.03-LTS-SP4 仓库镜像站的瞬时网络故障（HTTP/2 流异常断开），属于 infra-error。等待镜像站恢复后重新触发 CI 构建大概率通过。

## 需要进一步确认的点
如果多次重试仍持续失败，需排查以下方向：
1. 确认 `repo.****.org`（屏蔽域名的真实地址）的 HTTP/2 服务是否在特定时段存在稳定性问题
2. 检查 CI 构建环境的网络代理/网关是否对 HTTP/2 长连接有超时或断开策略
3. 确认是否只有 `gcc-c++-12.3.1-110` 这个特定 RPM 包持续下载失败（可能是该包在 CDN 节点上缓存损坏或文件不完整）
