# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Conan源下载403
- 新模式症状关键词: conan install, bzip2, 403 Forbidden, AuthenticationException, source(), build-3rdparty

## 根因分析

### 直接错误
```
#13 330.7 Downloading conan_sources.tgz
#13 331.0 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#13 331.8 ERROR: bzip2/1.0.8: Error in source() method, line 50
#13 331.8 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#13 331.8 	AuthenticationException: 403: Forbidden
#13 331.9 conan install failed
#13 331.9 make: *** [Makefile:263: build-3rdparty] Error 1
#13 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     ./scripts/install_deps.sh &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: Dockerfile:41-45 (`make build-cpp` → `make build-3rdparty` → `conan install` → bzip2/1.0.8 source 下载)
- 失败原因: Milvus C++ 构建的 `make build-3rdparty` 步骤通过 Conan 包管理器下载 `bzip2/1.0.8` 源码时，上游源站返回 HTTP 403 Forbidden，导致 Conan `source()` 方法抛出 `AuthenticationException`，整个构建链失败。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了 `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`（以及 README、image-info.yml、meta.yml 元数据更新）。Dockerfile 中构建命令 `make build-cpp` 及其触发的 `conan install` 步骤与已存在的 milvus 2.6.0 on 24.03-lts-sp2 版本逻辑相同，bzip2 源码下载 403 是上游源站/网络层面的问题，非 PR 代码引入。

## 修复方向

### 方向 1（置信度: 中）
**bzip2 官方源站禁止了 CI 环境的访问**。Conan 包 bzip2/1.0.8 默认从 `sourceware.org` 下载源码（`https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz`），该源站可能对特定 User-Agent、IP 段或无 Referer 的请求返回 403。修复方法：在 Dockerfile 中，于 `./scripts/install_deps.sh` 之前，手动将 bzip2 源码预下载到 Conan 缓存目录，或通过 Conan 的 `--remote` 参数指定备用镜像源（如 ConanCenter 其他 mirror）。

### 方向 2（置信度: 低）
**ConanCenter 的 bzip2 recipe source URL 已过时**。`bzip2/1.0.8` 的 Conan recipe 中硬编码的下载 URL 可能已失效或被迁移到新地址。可通过 `conan config` 或环境变量覆盖 bzip2 的 source URL 来解决。但此方向概率较低，因为同样的 recipe 在 milvus 2.6.0 on 24.03-lts-sp2 的 CI 构建中应已通过。

## 需要进一步确认的点
1. 确认已存在的 `Database/milvus/2.6.0/24.03-lts-sp2/Dockerfile` 在同一 CI 环境下是否能成功构建（验证是否为 24.03-lts-sp4 特有的网络问题或 bzip2 上游源站的全局变化）。
2. 确认 `sourceware.org/pub/bzip2/` 在当前 CI runner 网络环境中是否可达、是否返回 403。
3. 确认 milvus 2.6.0 使用的 Conan recipe（通常是 conan-center-index 中的 `bzip2/1.0.8`）中 `source()` 方法指向的具体下载 URL，并手动验证该 URL 的可达性。
4. 若该 403 是临时性的（源站短暂限流），可考虑触发 CI 重试确认是否稳定复现。
