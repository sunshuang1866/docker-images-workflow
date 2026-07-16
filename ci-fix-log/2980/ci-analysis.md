# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在通过 HTTP/2 协议分发 RPM 包时出现流传输中断（Curl error 92: INTERNAL_ERROR），导致 `cmake-data`、`git-core`、`gcc-c++` 三个包各经历一次或多次镜像重试。前两者最终从其他镜像成功下载，但 `gcc-c++` 重试 2 次后耗尽所有可用镜像，dnf 安装整体失败。

### 与 PR 变更的关联
与 PR 改动**无关**。PR 仅新增了一个正确的 Dockerfile（GrADS 2.2.3 + openEuler 24.03-lts-sp4 的编译安装流程）以及对应的 README、image-info.yml、meta.yml 元数据更新。失败纯粹由构建过程中 openEuler 软件仓库的镜像服务器 HTTP/2 协议故障引起，属于临时性基础设施问题。Dockerfile 中的 `dnf install` 命令本身语法正确、包名均有效（日志显示 dnf 成功解析了 258 个包的依赖关系并开始下载，且大部分包下载成功）。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 CI 基础设施的临时网络故障（openEuler 镜像服务器 HTTP/2 协议在构建期间不稳定）。建议等待镜像服务器恢复后重新触发 CI 构建（retry）。若反复出现同类问题，可考虑在 CI 层面为 dnf 配置 `retries` 和 `timeout` 参数，提高网络容错能力。

## 需要进一步确认的点
1. 确认 `repo.****.org`（openEuler 软件仓库镜像）在当前时间的可用性——是否存在已知的镜像站维护或 CDN 故障。
2. 若多次重试仍失败，排查是否为 CI runner 所在网络与镜像站之间的链路问题（如某段代理或防火墙对 HTTP/2 长连接的支持不佳）。
3. 确认 dnf 的默认重试机制是否足够——本次构建中 gcc-c++ 仅重试 2 次即耗尽镜像列表，日志中未显示 dnf 启用了额外的重试策略。
