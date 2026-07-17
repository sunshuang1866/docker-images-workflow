# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在通过 DNF 从 openEuler 24.03-LTS-SP4 RPM 仓库下载 `gcc-c++`（约 13MB）时，多次遭遇 HTTP/2 流层错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），DNF 重试所有可用镜像后仍无法下载该包，导致 `dnf install` 失败。日志中另有 3 个包（`cmake-data`、`git-core`、`gcc-c++` 首次尝试）也遇到同类 HTTP/2 流错误，但前两者重试后成功，仅 `gcc-c++` 在所有镜像均失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 语法和依赖声明均正确，`dnf install` 命令中的包名均在 openEuler 24.03-LTS-SP4 仓库中真实存在（`Dependencies resolved` 阶段已列出完整的 258 个安装包及依赖）。失败纯粹由 CI runner 与 openEuler 24.03-LTS-SP4 RPM 仓库镜像之间的网络传输问题（HTTP/2 RFC 9113 中的 `GOAWAY` 或 `RST_STREAM` 帧处理异常）导致，属于基础设施不稳定。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。HTTP/2 流错误通常是仓库端或网络中间件的**瞬时故障**，可尝试重新触发 CI 运行。若重试后依然失败，则需要排查 CI runner 到目标仓库的网络连接质量。

### 方向 2（置信度: 低）
若反复重试仍失败，可尝试在 Dockerfile 构建前禁用 HTTP/2 或强制使用 HTTP/1.1 进行 DNF 下载（通过修改 `/etc/dnf/dnf.conf` 添加代理设置或 curl 配置）。但这通常是临时规避手段，长期应排查仓库端 HTTP/2 服务配置。

### 方向 3（置信度: 低）
若问题持续且仅影响 24.03-LTS-SP4 仓库，可在 Dockerfile 第一行前添加 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 绕过 HTTP/2，但这属于规避而非修复。

## 需要进一步确认的点
1. 该错误是否在同时段内的其他 PR（针对 24.03-LTS-SP4 的构建）中也出现？如果是，说明 openEuler 24.03-LTS-SP4 仓库当时存在全局性问题。
2. 重试 CI 后问题是否自行消失？若消失则可确认是瞬时网络故障。
3. aarch64 架构 runner 上是否也出现了同类错误？日志中仅有 x86_64 构建信息，如 aarch64 通过则进一步说明是 x86_64 runner 到仓库的局部网络问题。
4. 目标仓库 `repo.****.org` 的 HTTP/2 服务端是否配置了过短的 `SETTINGS_MAX_CONCURRENT_STREAMS` 或丢包率较高导致 `GOAWAY` 帧频繁传输？
