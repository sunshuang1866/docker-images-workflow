# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Conan源下载403
- 新模式症状关键词: AuthenticationException, 403: Forbidden, bzip2, conan install failed, build-3rdparty, conan_sources.tgz

## 根因分析

### 直接错误
```
#13 317.3 Downloading conan_sources.tgz
#13 317.6 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#13 318.3 ERROR: bzip2/1.0.8: Error in source() method, line 50
#13 318.3 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#13 318.3 	AuthenticationException: 403: Forbidden
#13 318.4 conan install failed
#13 318.4 make: *** [Makefile:263: build-3rdparty] Error 1
#13 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     ./scripts/install_deps.sh &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:22-26`（`make build-cpp` 的 `build-3rdparty` 子目标）
- 失败原因: Milvus 2.6.0 的 C++ 构建系统通过 Conan（包管理器）下载第三方依赖时，`bzip2/1.0.8` 的 Conan recipe 在其 `source()` 方法中尝试从上游服务器下载源码包，服务器返回 403 Forbidden，导致 `conan install` 失败，整个 `make build-cpp` 中断。

### 与 PR 变更的关联
- PR 新增了 Milvus 2.6.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，本身语法正确、逻辑合理。
- 失败并非 Dockerfile 写法问题，而是 Milvus 构建系统的 Conan 依赖解析阶段，bzip2 1.0.8 的上游源码下载源返回 403，属于外部依赖可用性变化。
- 已有的 SP2 版本（`2.6.0/24.03-lts-sp2/Dockerfile`）如果当前重建，理论上也会遇到同样的 bzip2 下载 403 问题，因为使用的是同一个 Milvus 版本和同一套 Conan recipes。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 `make build-cpp` 之前，通过 Conan 配置或环境变量替换 bzip2 的下载源为可用镜像。例如：
- 在 `conan install` 前设置 bzip2 Conan recipe 的 `sources` URL 为替代镜像（如 `https://sourceware.org/pub/bzip2/` 或其他 CDN）。
- 或将 bzip2 的源码包提前下载到 Conan 本地缓存，绕过 recipe 的 `source()` 下载步骤。

### 方向 2（置信度: 低）
升级 bzip2 版本。Milvus 2.6.0 的 `conanfile` 或 Conan recipe 锁定了 `bzip2/1.0.8`，如果 Conan Center 的 bzip2 1.0.8 recipe 的下载源已整体失效，需要排查是否有更新的 bzip2 版本（如 1.0.9）可替代，并确认 Milvus 构建系统是否兼容。

### 方向 3（置信度: 低）
检查是否为临时网络问题。403 可能来自服务端的临时访问限制或 IP 风控，重新触发 CI 构建可能自动通过。

## 需要进一步确认的点
1. bzip2 1.0.8 的 Conan recipe（来自 conan-center）当前 `source()` 方法中配置的下载 URL 是什么，该 URL 在浏览器或 wget 中是否也返回 403。
2. 已有的 `2.6.0/24.03-lts-sp2/Dockerfile` 对应的 CI 构建是否已缓存了 Conan 包；如果清除缓存后重新构建 SP2 版本，是否也会触发相同的 bzip2 403 错误。
3. 该 403 是否为 CI 构建节点 IP 被上游服务器风控拦截所致（临时性），还是上游源已永久不可用。

## 修复验证要求
若采用方向 1（替换 bzip2 下载源），code-fixer 必须：
- 从 Conan Center 获取 bzip2/1.0.8 当前 recipe 的 `conanfile.py`，确认 `source()` 方法中的实际下载 URL。
- 验证替代下载源确实可公开访问且提供的是合法的 bzip2 1.0.8 源码包（SHA256 应与 Conan recipe 中的 `sha256` 值一致）。
- 若采用方式 2（升级 bzip2 版本），需确认 Milvus 2.6.0 的 Conan 依赖配置允许版本替换，且 C++ 构建不会因版本变更而产生编译或链接错误。
