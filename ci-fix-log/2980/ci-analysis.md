# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败原因: 在 `dnf install` 下载 258 个 RPM 包（总计 914 MB）的过程中，openEuler 24.03-LTS-SP4 仓库镜像站多次出现 HTTP/2 流错误（Curl error 92），导致 `gcc-c++` 包（13 MB）在所有已配置的镜像源上均下载失败，最终 `dnf` 因无可用镜像而报错退出。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了 `grADS 2.2.3` 在 `openEuler 24.03-LTS-SP4` 上的 Dockerfile（含 `dnf install` 构建依赖 30 行）及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 内容语法正确、依赖声明完整。构建失败的原因是 CI 运行环境中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站发生了间歇性 HTTP/2 传输错误，属于 CI 基础设施层面的瞬时网络故障。日志中可见 `cmake-data` 和 `git-core` 两个包在初始下载失败后通过镜像重试成功下载，仅 `gcc-c++` 因反复失败而最终耗尽所有镜像。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 该失败属于 openEuler 24.03-LTS-SP4 仓库镜像站的瞬时 HTTP/2 传输故障（Curl error 92），非 PR 代码问题。在 PR 中评论触发 CI 重新构建（recheck / retest），仓库镜像站在网络稳定时通常可正常提供服务。

## 需要进一步确认的点
- 如果多次重试后仍持续失败，需要排查 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 配置稳定性，或考虑在 CI 构建环境中对 `dnf` 配置添加 `retries` 及 `timeout` 参数以增强对瞬时网络波动的容忍度。
- 确认 CI 构建节点到 `repo.****.org` 的网络链路是否稳定（是否存在代理或中间层导致 HTTP/2 流被异常关闭）。
