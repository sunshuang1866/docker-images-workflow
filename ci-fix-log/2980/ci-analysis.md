# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, No more mirrors to try

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
- 失败原因: CI 构建环境在 `dnf install` 阶段通过 HTTP/2 协议从 openEuler 仓库镜像站下载 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer）。受影响的包包括 `cmake-data`、`git-core` 和 `gcc-c++`。其中 `cmake-data` 和 `git-core` 经重试后成功下载，但 `gcc-c++` 在所有镜像重试耗尽后仍然失败（`No more mirrors to try`），导致 dnf 安装整体失败。

### 与 PR 变更的关联
**与 PR 无关。** 该失败由 CI 构建环境与 openEuler 仓库镜像站之间的网络/HTTP/2 协议通信问题导致，属于基础设施层面故障。新增 Dockerfile 中的 `dnf install` 命令语法正确，所列包名均在 openEuler 24.03-LTS-SP4 仓库中存在（日志中 dnf 已成功解析依赖并部分下载了 40/258 个包）。PR 的元数据文件变更（README.md、image-info.yml、meta.yml）也不涉及构建逻辑。

## 修复方向

### 方向 1（置信度: 中）
**重试构建。** 该错误为网络层面的间歇性故障（HTTP/2 流中断），两次出现于仓库镜像的 HTTP/2 连接中。考虑到 `cmake-data` 和 `git-core` 经重试后成功，而 `gcc-c++` 恰好耗尽所有镜像重试次数，属于小概率事件。重新触发 CI 构建有较大概率成功。

### 方向 2（置信度: 低）
**在 dnf 安装前添加重试/镜像配置。** 如果同一镜像持续失败，可考虑在 Dockerfile 中为 `dnf` 添加重试参数（如 `--setopt=retries=10`），或显式指定使用 HTTP/1.1 协议（`echo "http2=false" >> /etc/dnf/dnf.conf`），以规避 HTTP/2 流错误。但目前无法确定该错误是永久性还是暂时性，证据不足以建议直接修改 Dockerfile。

## 需要进一步确认的点
1. 该错误是否为一次性的网络波动，还是 openEuler 24.03-LTS-SP4 仓库镜像站 x86_64 的持续性问题——需要重试构建至少 2-3 次来验证。
2. 如果多次重试后 `gcc-c++` 下载仍然失败，需要确认 openEuler 24.03-LTS-SP4 仓库的 gcc-c++ RPM 包本身是否存在（日志显示 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`，dnf 已正确解析依赖树，初步判断包本身存在）。
3. 其他同一批 PR 中是否有类似失败模式，用于判断是否为仓库侧的全量问题。
