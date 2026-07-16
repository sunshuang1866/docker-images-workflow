# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.****.org, dnf install

## 根因分析

### 直接错误

多个 RPM 包在下载时遭遇 HTTP/2 流错误：

```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库（`repo.****.org`）在处理 HTTP/2 请求时反复出现流协议错误（`INTERNAL_ERROR`），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载中断。builder 阶段的 `gcc` 包在重试所有镜像后仍下载失败，dnf 安装过程被终止。第二个阶段（stage-1）虽然在部分包上通过重试成功，但最终因 builder 阶段失败而被整体取消（`CANCELED`）。

### 与 PR 变更的关联

**与 PR 无关。** PR 的变更仅限于新增一个合法的 Dockerfile（含正确的 dnf 依赖声明和 Makefile 补丁）及配套的 README、meta.yml、image-info.yml 更新。失败的直接原因是 openEuler 24.03-LTS-SP4 RPM 仓库的 HTTP/2 基础设施在 CI 执行期间不稳定，Dockerfile 本身没有语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施问题——openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 CI 运行期间出现了间歇性的 HTTP/2 流错误。处理方式为：
- 等待仓库服务恢复后重新触发 CI 构建（retry）
- 该问题通常会自行恢复，属于临时性基础设施波动

## 需要进一步确认的点

- 确认 `repo.****.org`（被屏蔽的仓库域名）是否为 openEuler 24.03-LTS-SP4 的官方 RPM 仓库，以及该仓库当前是否存在已知的 HTTP/2 服务中断
- 确认同一次 CI 运行中其他使用 sp4 基础镜像的 job 是否也出现了相同的 dnf 下载错误（可用于佐证是否为仓库侧全局问题）
- 如果该问题在多次重试后持续出现，可能需要将 dnf 配置中的 HTTP/2 回退为 HTTP/1.1（`http2=0`）以绕过该错误
