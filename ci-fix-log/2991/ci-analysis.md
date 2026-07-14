# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 构建节点在执行 `dnf install -y git gcc gcc-c++ make cmake` 时，从 `repo.openeuler.org` 下载 RPM 包（`git-core`、`gcc-c++`、`guile`）反复遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），最终 `guile` 包耗尽所有镜像重试后下载失败，导致整个 dnf 命令退出码为 1。该错误与 PR 新增的 Dockerfile 代码无关，属于 openEuler 24.03-LTS-SP4 aarch64 仓库的服务器端 HTTP/2 协议层瞬时故障。

### 与 PR 变更的关联
PR 新增了一个标准的 vvenc Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令本身语法正确、包名无误。失败发生在下游仓库包下载阶段，属于 openEuler 官方镜像仓库 `repo.openeuler.org` 的 HTTP/2 服务端瞬时异常，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
触发 CI 重试（retrigger / re-run）。该失败为仓库服务器端 HTTP/2 流瞬时中断导致，属于基础设施问题，不是代码缺陷。重试大概率可以通过（日志显示部分受影响的包如 `git-core` 已在后续重试中下载成功，`guile` 只是恰好在一轮重试中耗尽尝试次数）。

### 方向 2（置信度: 低）
若重试持续失败，可在 Dockerfile 的 `dnf install` 前设置环境变量 `RUST_CURL_HTTP2=0` 或调整 dnf 的 HTTP/2 行为（如 `echo "http2=false" >> /etc/dnf/dnf.conf`）强制使用 HTTP/1.1 绕过 HTTP/2 流层错误。但目前无证据表明这是持续性问题，不建议提前应用此修改。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 的 HTTP/2 服务是否已恢复稳定（可通过手动 `curl -I --http2 https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 验证）。
- 如果重试仍然失败且怀疑是 SP4 仓库的持久性问题，需联系 openEuler 基础设施团队排查 CDN/负载均衡器的 HTTP/2 配置。
