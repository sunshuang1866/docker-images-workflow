# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 软件源（`repo.****.org`）的 HTTP/2 服务端在下载过程中多次返回 `INTERNAL_ERROR`，导致 stream 异常关闭。虽然 `cmake-data` 和 `git-core` 通过重试其他镜像成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（约 13MB 的大包）在两次重试后所有镜像均返回相同错误，最终 `dnf install` 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（以及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 中的 `dnf install` 包列表语法正确、包名合理。失败完全由 openEuler 24.03-LTS-SP4 软件源服务器的 HTTP/2 实现缺陷引发，属于 CI 基础设施层面的问题。Code Fixer 无需对 PR 代码做任何修改。

## 修复方向

### 方向 1（置信度: 高）
此失败属于 CI 基础设施问题（软件源 HTTP/2 服务端不稳定），与 PR 代码变更无关。建议触发**重新运行 CI Job**（retry/re-run），等待软件源服务恢复正常后构建即可通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果多次重试均失败，可能是该特定 RPM 包（gcc-c++-12.3.1-110.oe2403sp4）在镜像站上确实损坏或同步不完整。此时需要联系 openEuler 基础设施团队检查 `repo.****.org` 镜像站的同步状态和 HTTP/2 代理配置。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 HTTP/2 反向代理（如 nginx/haproxy）配置是否正确，是否存在对大文件传输的 HTTP/2 stream 超时或 buffer 限制。
- 确认镜像站与上游 openEuler 主站之间的 RPM 同步是否完整，`gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 文件是否完整未损坏。
- 同一时间段内其他 openEuler 24.03-LTS-SP4 的 Dockerfile 构建是否也出现了相同错误（可用于判断是否为软件源全局性问题）。
