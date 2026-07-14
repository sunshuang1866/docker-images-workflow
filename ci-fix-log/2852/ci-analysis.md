# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Conan源下载认证失败
- 新模式症状关键词: conan install failed, AuthenticationException, 403: Forbidden, bzip2, source() method, build-3rdparty

## 根因分析

### 直接错误
```
#13 305.9 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#13 308.4 ERROR: bzip2/1.0.8: Error in source() method, line 50
#13 308.4 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#13 308.4 	AuthenticationException: 403: Forbidden
#13 308.5 conan install failed
#13 308.5 make: *** [Makefile:263: build-3rdparty] Error 1
#13 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     ./scripts/install_deps.sh &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: Dockerfile:22-26（`make build-cpp` 步骤中的 `make build-3rdparty` 子步骤）
- 失败原因: Milvus `make build-cpp` 构建流程调用 `conan install` 安装第三方依赖时，conan 在下载 `bzip2/1.0.8` 源码阶段失败，源码服务器返回 HTTP 403 Forbidden（`AuthenticationException`），导致 `make build-3rdparty` 返回错误码 1，进而 `make build-cpp` 失败（exit code 2）。

### 与 PR 变更的关联
PR 变更仅为新增一个 Milvus 2.6.0 的 Dockerfile（+53 行）、更新 README.md 镜像表格、更新 image-info.yml 和 meta.yml。这些变更本身不引入任何编译代码或依赖版本变动。失败发生在 `make build-cpp` 的第三方依赖构建阶段（conan 下载 bzip2 源码），与 PR 的 Dockerfile/元数据变更无因果关系——即使按相同构建流程重建已有 SP2 版本的 Dockerfile，若 conan 源状态不变，同样会失败。

## 修复方向

### 方向 1（置信度: 中）
Conan 配方中 `bzip2/1.0.8` 的源码下载 URL 已失效或需要认证。检查 conan 中心/远程仓库中 bzip2/1.0.8 配方的 `sources` 定义，确认当前指定的下载 URL 是否可用。如果上游 URL 已变更，需要在 Dockerfile 中通过 conan 配置覆盖镜像源，或者在 `make build-cpp` 前通过 conanfile 补丁替换 bzip2 的下载地址。

### 方向 2（置信度: 低）
若 conan 源码 URL 本身有效但被 CI 构建环境的出口 IP 触发反爬/防滥用策略拦截，则需在 CI 层面配置代理或将 conan 源切换至内部镜像缓存。

## 需要进一步确认的点
1. conan 远程仓库（如 conancenter）中 `bzip2/1.0.8` 配方的 `conandata.yml` 里 `sources` 字段指向的具体下载 URL 是否可公开访问。
2. 该 URL 在 CI 构建环境外（如本地或浏览器）是否同样返回 403。
3. 对比已有成功构建的 Milvus 2.6.0 SP2（`24.03-lts-sp2`）版本的 CI 日志，确认其构建时期 bzip2 下载是否也曾遇到同样问题（以判断是否为近期上游变更导致的回归）。
4. 是否存在可用的 conan 镜像源（如华为云 conan 镜像）可绕过此 403 问题。
