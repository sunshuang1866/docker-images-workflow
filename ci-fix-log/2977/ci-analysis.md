# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源网络传输异常
- 新模式症状关键词: Curl error, HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors, repo.openeuler.org, Error downloading packages

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`
- 失败原因: Docker 构建在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 仓库的 HTTP/2 传输层出现 `INTERNAL_ERROR`，导致 173 个需下载的包中，前 172 个下载完成（含 gcc、kernel-headers 等重试后成功的包），但第 173 个包 `vim-common` 下载失败且无备用镜像可用，yum 事务因包下载不完整而终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增的 Dockerfile 中 `yum install` 命令语法正确，安装的包列表均为 openEuler 24.03-LTS-SP4 仓库中存在的合法包。失败是 CI 构建时 `repo.openeuler.org` 仓库服务器的 HTTP/2 层发生了瞬时传输错误（`INTERNAL_ERROR`、`SSL_ERROR_SYSCALL`）所导致，属于 CI 基础设施层面的网络波动问题。`vim-common` 也并非 Dockerfile 显式声明的包，而是作为某个显式包的间接依赖被 yum 自动拉取的。

日志中有多处类似错误但 succeeded on retry：
- `gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92)` → 重试后成功下载
- `kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92)` → 重试后成功下载
- `perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56)` → 重试后成功下载
- `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92)` → 无更多镜像可尝试，最终失败

这表明仓库服务器在该时间段内 HTTP/2 连接不稳定，是一个暂时性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败是由 openEuler 官方仓库 `repo.openeuler.org` 在构建期间的瞬时网络/HTTP/2 服务端异常导致，与 Dockerfile 内容或 PR 变更无关。直接触发 re-run 即可，极大概率会通过。无需对代码做任何修改。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在该时间段是否有已知的服务端故障或维护。
- 如果同一 PR 多次重试均失败且同一个包（`vim-common`）持续出错，则可能需要联系 openEuler 仓库维护方排查该特定 RPM 包的 CDN/镜像同步状态。
