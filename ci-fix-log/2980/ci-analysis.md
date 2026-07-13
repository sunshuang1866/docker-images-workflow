# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源 HTTP/2 流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 软件源（`repo.****.org`）的多个镜像站返回 HTTP/2 流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），导致 `gcc-c++` 等 RPM 包下载失败。`dnf` 在尝试所有可用镜像后均失败，最终退出码为 1。

### 与 PR 变更的关联
与 PR 变更**无直接关系**。PR 新增的 Dockerfile 本身语法正确、依赖声明完整（`dnf install` 的包列表合法），构建失败纯粹由 CI 基础设施中的软件源 HTTP/2 连接不稳定导致。日志中可见多个包（`cmake-data`、`git-core`、`gcc-c++`）均遭遇同类 Curl 92 错误，其中 `git-core` 在重试后成功下载，而 `gcc-c++` 耗尽所有镜像后仍失败，这进一步证明了问题是临时的网络/服务端抖动，而非 Dockerfile 内容有误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可**。该失败为 CI 基础设施中的软件源 HTTP/2 连接瞬时故障，与 PR 代码变更无关。等待镜像站恢复后重新触发 CI 构建，大概率会通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果该软件源 HTTP/2 问题持续出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加重试参数（如 `--setopt=retries=10`），或临时将 `dnf` 回退为 HTTP/1.1（通过设置 `ip_resolve=4` 或禁用 HTTP/2），以规避 HTTP/2 层的流错误。但不推荐对偶发基础设施问题做此类代码级 workaround。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 软件源是否为近期新增或迁移的镜像站，是否存在 HTTP/2 配置不稳定的已知问题。
- 如果后续多次触发 CI 构建仍然在相同镜像站失败，需要联系基础设施团队排查镜像站 HTTP/2 代理/负载均衡器的健康状态。
- 其他基于 `openeuler:24.03-lts-sp4` 的新增 PR 是否也遇到同样的软件源 Curl 92 错误——若有，则确认是源站侧问题。
