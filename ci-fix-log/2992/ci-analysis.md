# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库服务器在处理 HTTP/2 连接时不稳定，多个包的下载过程中出现 `Stream error in the HTTP/2 framing layer`（Curl error 92），其中大体积的 `gcc` 包（34 MB）经多次镜像重试后均失败，最终 dnf 放弃安装，导致构建中断。stage-1（#7）同样经历了多次 HTTP/2 流错误但最终靠重试成功（仅 32 个包），而 builder（#8）需要安装 157 个包（261 MB），gcc 包重试耗尽后失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个合法的 Dockerfile（sp4 变体）及对应的 README、image-info.yml、meta.yml 条目，Dockerfile 中的 `dnf install` 命令写法与已有的 sp3 版本一致。失败是由 openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 协议层不稳定引起的，属于 CI 基础设施/上游仓库的网络问题。

## 修复方向

### 方向 1（置信度: 中）
**等待上游仓库恢复后重试。** 该错误为 openEuler 24.03-LTS-SP4 软件包仓库的 HTTP/2 服务端暂时性故障（服务端在 HTTP/2 流传输中发送了 `INTERNAL_ERROR` 并断开连接），通常在几小时到几天内恢复。可等待仓库服务恢复后重新触发 CI 构建。若多次重试后仍然失败，可考虑在 `dnf install` 前添加重试/容错逻辑（如设置 `--retries` 或循环重试）。

### 方向 2（可选，置信度: 低）
**通过 dnf 配置降级为 HTTP/1.1。** 在 RUN 命令中配置 curl 禁用 HTTP/2（`echo "http2=false" >> /etc/dnf/dnf.conf` 或设置环境变量），绕过 HTTP/2 协议层的不稳定，改用 HTTP/1.1 下载包。但这属于规避方案而非根因修复，且可能降低下载效率。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 服务状态是否已恢复（可在构建节点上手动 `curl --http2 -v` 测试包下载 URL 确认）。
2. 本次失败是否为偶发性网络抖动——建议在不修改任何代码的情况下重试 CI 至少 2 次，观察是否稳定复现。
3. 同仓库其他使用 24.03-LTS-SP4 的镜像（如 PR #3139 `AI/open-webui`、PR #3135 `AI/oneapi-basekit` 等）近期是否也出现了类似的 HTTP/2 stream 错误——若有，则确认是上游仓库的普遍性问题而非 PR 个例。
