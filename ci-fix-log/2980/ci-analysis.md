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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 DNF 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层流错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），gcc-c++ 经多次重试失败后 `dnf install` 退出码为 1，构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 GrADS 2.2.3 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 内容为标准的 `dnf install` 构建依赖列表 + 源码编译流程，列表中的包名全部合法且在仓库中真实存在（DNF 成功解析了 258 个包的依赖关系）。失败完全由 openEuler 软件仓库服务器端 HTTP/2 协议问题导致，属于 CI 基础设施临时故障，非代码错误。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务端协议临时故障（`INTERNAL_ERROR` 来自服务端主动关闭流），与 Dockerfile 内容无关。重新触发构建即可，无需修改任何代码。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时段是否存在已知服务端问题。
- 如果同一仓库 URL 在短时间内多次构建均出现同类 HTTP/2 错误，需联系仓库运维排查服务端 HTTP/2 配置或降级为 HTTP/1.1。
