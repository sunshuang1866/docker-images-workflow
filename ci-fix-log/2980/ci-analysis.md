# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 的 RPM 仓库（repo.****.org）在 HTTP/2 传输层出现流错误（`Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2)`）。多个包（cmake-data、git-core、gcc-c++）均遭遇此错误，其中 cmake-data 和 git-core 在重试后下载成功，但 gcc-c++ 两次重试均失败，最终因 "No more mirrors to try" 导致 `dnf install` 命令退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 在语法和包依赖声明上均正确——列出的所有包都存在于仓库的元数据中（Dependencies resolved 步骤正常完成，258 个包的事务摘要已生成）。失败发生在 `dnf` 实际下载 RPM 包阶段，是 openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 实现问题导致传输层中断，属于 CI 基础设施 / 上游仓库可用性问题。

## 修复方向

### 方向 1（置信度: 中）
**重试触发 CI**。该错误为仓库服务器端 HTTP/2 流传输的偶发性问题（INTERNAL_ERROR 是服务端主动关闭流的错误码），并非代码缺陷。在仓库服务恢复正常后，重新触发 CI 大概率可以通过。Code Fixer 无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 低）
**降级 curl 的 HTTP 版本**。如果在 Dockerfile 构建步骤中为 `dnf` 配置强制使用 HTTP/1.1 可绕过此问题。但这属于对上游基础设施问题的规避性 workaround，不属于代码修复，且不保证仓库未来行为的兼容性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（repo.****.org）的 HTTP/2 服务是否已恢复正常。可通过手动 `curl --http2 -I <repo URL>` 或重试 CI 来验证。
- 如果多次重试 CI 均失败，需排查仓库服务器端是否存在 HTTP/2 配置问题或负载过高导致的流中断。
