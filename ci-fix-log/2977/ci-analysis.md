# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库临时不可用
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, yum install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer ...
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 构建节点（aarch64）在 `yum install` 下载 173 个 RPM 包过程中，`repo.openeuler.org` CDN 的 HTTP/2 连接发生多次流层错误（Curl error 92: `INTERNAL_ERROR`）和 SSL 读取失败（Curl error 56）。前三个受影响的包（gcc、kernel-headers、perl-MIME-Base64）通过 yum 内置重试机制下载成功，但第 173 个包（vim-common）重试耗尽所有 mirror 后仍然失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个完全正确的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法和包名均无误，失败纯粹由 `repo.openeuler.org` 仓库 CDN 在构建期间的临时网络抖动导致。相同的 Dockerfile 在重新触发 CI 后极大概率会构建成功（日志中 gcc、kernel-headers 等包最初失败但重试后成功即证明网络问题为临时性的）。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 `repo.openeuler.org` CDN 临时性 HTTP/2 流层错误，属基础设施问题，无需修改任何代码或 Dockerfile。直接重新运行失败的 CI job 即可。

## 需要进一步确认的点
无。日志中的错误信息清晰直指 `repo.openeuler.org` CDN 的 HTTP/2 传输层临时故障，与 PR 代码无关。

## 修复验证要求
不适用——本次失败为 infra-error，无需代码修复。
