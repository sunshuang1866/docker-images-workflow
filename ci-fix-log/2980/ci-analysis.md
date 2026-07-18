# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo mirror, INTERNAL_ERROR (err 2)

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
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）下载 RPM 包时，多次遭遇 HTTP/2 协议层面的流错误（Curl error 92: INTERNAL_ERROR），涉及 `cmake-data`、`git-core`、`gcc-c++` 三个包。其中 `gcc-c++` 在所有镜像源均失败后 dnf 放弃安装，导致 Docker 构建第 [2/3] 步退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增了一个完全合法的 Dockerfile，`dnf install` 命令语法正确，所列包名在 openEuler 24.03-LTS-SP4 仓库中均存在（日志中 `Dependencies resolved` 阶段列出了全部 258 个包及其版本号，说明仓库元数据解析正常）。失败纯粹由 CI 构建节点与 openEuler 包仓库之间的 HTTP/2 网络连接不稳定造成——上游仓库服务器在 HTTP/2 流传输过程中异常关闭了连接。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 CI 基础设施网络问题，属于临时性故障。建议触发重新构建（retry），大部分情况下同一节点重试或调度到不同节点即可绕过该网络波动。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在 CI 构建时间段内是否有服务端维护或 CDN 抖动记录。
- 如果多次重试后 3 个包（cmake-data、git-core、gcc-c++）中的某一个持续失败，可能是该特定 RPM 文件在仓库存储节点上损坏，需联系仓库维护方排查。
- 若需提高容错性（非本次 PR 必要改动），可在 Dockerfile 中为 `dnf install` 添加 `--setopt=retries=10` 增加重试次数，或将 `dnf` 配置中的 HTTP/2 降级为 HTTP/1.1（`echo "http2=false" >> /etc/dnf/libcurl.cfg`），但这属于通用优化而非本次故障的根因修复。
