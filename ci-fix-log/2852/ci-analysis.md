# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式 (参考模式04)
- 新模式标题: Conan bzip2 源 403
- 新模式症状关键词: bzip2/1.0.8, conan, AuthenticationException, 403 Forbidden, source() method, bzip2_source_fix.py

## 根因分析

### 直接错误
```
#14 293.5 [HOOK - bzip2_source_fix.py] pre_source(): Patched bzip2/1.0.8 source URLs to use working mirrors
#14 293.5 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#14 294.3 ERROR: bzip2/1.0.8: Error in source() method, line 50
#14 294.3 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#14 294.3 	AuthenticationException: 403: Forbidden
#14 294.4 conan install failed
#14 294.4 make: *** [Makefile:263: build-3rdparty] Error 1
#14 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     ./scripts/install_deps.sh &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:47-51`（`make build-cpp` → `make build-3rdparty` → `conan install` 步骤）
- 失败原因: Conan 包管理器在安装 Milvus C++ 第三方依赖时，`bzip2/1.0.8` 的 `source()` 方法尝试从上游下载 bzip2 源码，目标 URL 返回 HTTP 403 Forbidden。构建环境中已加载了 `bzip2_source_fix.py` 钩子试图将 URL 替换为可用镜像，但替换后的 URL 仍然失败（403），最终导致 `conan install` 失败，`make build-3rdparty` 返回错误码 1。

### 与 PR 变更的关联

**PR 变更直接触发了该失败**。该 PR 新增了一个完整的 Milvus 2.6.0 Dockerfile（全新文件），Dockerfile 第 47 行的 RUN 指令执行 `make build-cpp`，其中 `build-3rdparty` 目标依赖 Conan 下载编译第三方库（包括 bzip2/1.0.8）。由于上游 bzip2 下载源当前返回 403，Conan 无法完成依赖安装。

需要注意：同仓库中已存在 `Database/milvus/2.6.0/24.03-lts-sp2/Dockerfile`（SP2 版本），其构建设计与 SP4 版本相同。若 SP2 版本的 CI 构建当前也失败，则说明是上游源的整体性问题；若 SP2 能正常构建，则说明 `bzip2_source_fix.py` 钩子对 SP2 环境有效但对 SP4 环境无效（例如钩子依赖特定的 Conan 缓存状态或镜像源可用性差异）。但根据当前日志，无法确认 SP2 的构建状态。

## 修复方向

### 方向 1（置信度: 中）
**在 Dockerfile 中为 Conan 配置可用的 bzip2 镜像源**。在 `pip install conan==1.61.0` 之后、`make build-cpp` 之前，添加一个 Conan 配置步骤，通过 `conan config set` 或创建自定义 Conan recipe 来覆盖 bzip2/1.0.8 的 `source()` 方法中的下载 URL，指向一个确认可用的镜像源（如 `https://sourceware.org/pub/bzip2/` 或其他已验证可用的 CDN/镜像）。需先确认哪个镜像源在当前 CI 环境中可达。

### 方向 2（置信度: 低）
**升级 `bzip2_source_fix.py` 钩子中的镜像 URL 列表**。当前钩子尝试修补 bzip2 源 URL 但修补后的 URL 仍然返回 403。若该钩子是 CI 基础设施的一部分（位于 CI runner 上而非镜像仓库内），则需要在 CI 基础设施层面更新钩子脚本中的备用镜像 URL。但这超出了 PR 层面的修改范围。

### 方向 3（置信度: 低）
**升级 bzip2 的 Conan 版本或使用替代的 bzip2 配方**。Milvus 的 `conanfile.py` 中引用的 bzip2/1.0.8 可能是旧版本，上游 Conan Center 可能已有更新版本的配方使用了不同的下载源。但这需要修改 Milvus 源码中的 conanfile，工作量较大且可能引入其他兼容性问题。

## 需要进一步确认的点

1. **验证 SP2 构建状态**：同仓库中 `Database/milvus/2.6.0/24.03-lts-sp2/Dockerfile` 当前能否正常通过 CI 构建？如果 SP2 也失败，说明是上游 bzip2 源的普遍性问题；如果 SP2 成功，则需要排查 SP4 环境特有的差异。
2. **确认 bzip2 下载源的可达性**：在 CI runner 环境中手动测试 `bzip2_source_fix.py` 钩子修补后的 URL 是否可达（403 是否为临时故障），需要 SSH 到 runner 或查看 bzip2_source_fix.py 的具体实现来确认实际被访问的 URL。
3. **检查其他依赖是否有类似问题**：bzip2 是第一个失败的依赖，Conan 安装是按顺序进行的。即使修复了 bzip2 的下载问题，后续依赖也可能遇到类似的 403 问题，需要整体评估 Conan 依赖源在 openEuler 24.03-LTS-SP4 环境下的可用性。

## 修复验证要求

若采用方向 1（Dockerfile 中配置 Conan 镜像源），code-fixer 必须：
1. 在提交前确认所选替代下载源在 CI runner 环境中可达（可通过在同类 SP4 Dockerfile 中添加 `curl -I <URL>` 先行验证）。
2. 确认 `conan config set` 或自定义 recipe 的语法与 Conan 1.61.0 版本兼容。
3. 验证修复后 Docker 镜像能完整通过 `make build-cpp` 和 `make build-go` 两个阶段。
