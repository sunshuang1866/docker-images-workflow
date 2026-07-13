# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, stream error, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: Docker 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包遭遇 Curl 错误 92（HTTP/2 流帧层错误，服务端返回 `INTERNAL_ERROR`）。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++`（约 13 MB）两次尝试均失败，最终 dnf 报 "No more mirrors to try"，导致构建退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及配套的元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名有效，失败根因为 openEuler 24.03-LTS-SP4 官方仓库的 HTTP/2 服务端在传输大型 RPM 包时出现协议层内部错误，属于 CI 基础设施/上游仓库的网络问题。此失败为偶发性 transient error，retry 大概率可以通过。

## 修复方向

### 方向 1（置信度: 中）
**方案: retry 重试构建。** 本失败是上游仓库 HTTP/2 服务端瞬时错误导致的网络下载失败，与代码无关。直接重新触发 CI 构建即可，无需修改任何代码。

### 方向 2（置信度: 低）
**方案: 在 Dockerfile 中为 dnf 增加重试/降级参数。** 若该仓库持续出现 HTTP/2 不稳定问题，可在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `ip_resolve=4` 规避 HTTP/2 协议层问题。但这属于绕过而非修复，不是推荐方向。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端稳定性：是否存在持续性问题，还是仅本次构建遇到的瞬时故障。
- 同一 CI runner 上其他构建是否也遇到了类似的 Curl error (92)。若其他 PR 的同一仓库在相近时间也出现此错误，则说明是上游仓库侧问题。
- `gcc-c++` 包（13 MB）比其他同样出现 Curl error (92) 但重试成功的小包更容易触发 HTTP/2 流中断，可能与传输时长/数据量有关，可检查上游 CDN/代理的 HTTP/2 流超时配置。
