# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: Dockerfile:6（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在下载 RPM 包时多次出现 Curl error (92) —— HTTP/2 流被对端异常关闭（`INTERNAL_ERROR`），DNF 重试所有可用镜像后均失败，最终 `gcc-c++` 包无法下载，导致 dnf install 失败（exit code: 1）

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了一个 GrADS 2.2.3 的 Dockerfile 及对应的文档/元数据文件。Dockerfile 中的 `dnf install` 命令语法完全正确，DNF 成功解析了所有 258 个待安装包的依赖关系。失败发生在纯粹的网络下载阶段——openEuler 软件仓库的 HTTP/2 服务端在传输过程中多次异常关闭流，这是基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
这是 openEuler 24.03-LTS-SP4 软件仓库镜像的临时性网络故障，**Code Fixer 无需处理**。等待 CI 基础设施恢复后重新触发构建即可。此类 HTTP/2 stream error 通常由仓库镜像服务端的负载均衡器或反向代理临时故障引起，非客户端或代码问题。

### 方向 2（可选）
如果该问题持续出现，可以考虑在 Dockerfile 的 `dnf install` 之前添加重试机制或降低并发连接数以规避 HTTP/2 多路复用导致的流中断，但这属于规避手段而非根因修复。根因应在 openEuler 基础设施侧解决。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 OS 仓库镜像当前是否正常运行（可直接在浏览器中访问 `https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 验证）
- 如果同一时间段其他 PR 也使用 24.03-lts-sp4 基础镜像，检查它们是否也遇到相同的 Curl error (92)，以确认是否为仓库侧系统性故障
- 对比 SP3 版本的同类 Dockerfile（如 `Others/grads/2.2.3/24.03-lts-sp3/Dockerfile`）的 CI 是否在同一时间正常通过，以排除软件包列表本身的问题
