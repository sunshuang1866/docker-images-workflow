# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), MIRROR, dnf install, rpm download

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
- 失败原因: Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包的下载均遇到 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`，错误码 `INTERNAL_ERROR (err 2)`）。涉及的包包括 `cmake-data`、`git-core`、`gcc-c++`，其中 `gcc-c++` 重试失败次数最多（2 次 HTTP/2 流错误），最终耗尽所有镜像后下载失败，导致整个 `dnf install` 命令返回 exit code 1。这是典型的 CI 基础设施网络/镜像服务器问题，而非代码错误。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，安装的包列表也是 openEuler 24.03-LTS-SP4 仓库中实际存在的包（依赖解析阶段成功列出了所有 258 个待安装包，未报任何包名不存在）。失败仅由下载阶段仓库镜像的 HTTP/2 传输层问题导致，属于临时性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。错误根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器在本次 CI 运行期间存在 HTTP/2 流不稳定问题，属于临时性网络/服务端故障。Code Fixer 无需对代码做任何修改，直接触发 CI 重跑即可。历史经验表明，同类镜像服务器临时性问题通常在重试后消失。

### 方向 2（置信度: 低）
如果多次重试仍然复现同样的 HTTP/2 流错误，可考虑在 Dockerfile 中为 `dnf install` 添加 `--setopt=retries=10` 参数增加重试次数，或在前置步骤中强制 dnf 使用 HTTP/1.1（通过设置环境变量或 dnf 配置禁用 HTTP/2），以规避镜像服务器的 HTTP/2 实现缺陷。但此方向仅应在持续复现时才考虑。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时间段（2026-07-13 07:04 UTC 前后）是否存在已知的 HTTP/2 服务端异常或 CDN 节点故障。
- 如果该镜像在 aarch64 runner 上也触发构建（meta.yml 中未设置 `arch` 约束），需确认 aarch64 的构建日志是否也有相同问题，以区分是单节点网络问题还是镜像服务端全局问题。

## 修复验证要求
无需代码修改，无需额外验证步骤。直接重试 CI 即可。
