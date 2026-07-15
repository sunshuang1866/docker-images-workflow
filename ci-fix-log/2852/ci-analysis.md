# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Conan依赖源下载403
- 新模式症状关键词: conan install failed, AuthenticationException 403, bzip2, Error in source() method, build-3rdparty

## 根因分析

### 直接错误
```
#13 444.6 [HOOK - bzip2_source_fix.py] pre_source(): Patched bzip2/1.0.8 source URLs to use working mirrors
#13 444.6 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#13 445.4 ERROR: bzip2/1.0.8: Error in source() method, line 50
#13 445.4 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#13 445.4 	AuthenticationException: 403: Forbidden
#13 445.5 conan install failed
#13 445.5 make: *** [Makefile:263: build-3rdparty] Error 1
#13 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     ./scripts/install_deps.sh &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:42-46`（`make build-cpp` 步骤触发的 `build-3rdparty` 目标）
- 失败原因: Milvus 构建流程中 `make build-cpp` → `make build-3rdparty` 调用 Conan 包管理器安装第三方依赖。Conan 的 `bzip2/1.0.8` recipe 在 `source()` 方法中尝试从配置的 URL 下载 bzip2 源码 tarball，所有源均返回 HTTP 403 Forbidden。构建环境中虽存在 `bzip2_source_fix.py` 钩子尝试修复 URL，但钩子修补后的 URL 仍然不可用（同样返回 403）。

### 与 PR 变更的关联
PR 变更是纯粹的新增操作：添加了 `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`（新文件，53 行）、更新了 `README.md` 和 `image-info.yml` 以添加新 tag 条目、更新了 `meta.yml` 以注册新版本路径。

Dockerfile 中的构建命令 `./scripts/install_deps.sh && make build-cpp && make build-go` 是 Milvus 的标准构建流程，与 PR 的 Dockerfile 编写方式无关。该失败属于 Conan 上游依赖源（bzip2 1.0.8 的下载 URL）可用性问题，即使用同样的构建命令在已有的 SP2 Dockerfile 上重新触发构建，也可能遇到相同错误。**失败并非由 PR 代码变更引入的逻辑缺陷导致**，而是 Conan 包管理器尝试下载 bzip2 1.0.8 源码时所有可用镜像均返回 403。

## 修复方向

### 方向 1（置信度: 中）
更新构建环境中 `bzip2_source_fix.py` 钩子脚本，将 bzip2 1.0.8 的下载 URL 替换为当前可用的镜像源（如 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 或通过 `repo.huaweicloud.com` 等已验证可达的镜像站提供该文件）。需确认目标 URL 可从 CI 构建环境正常下载且 hash 值与 Conan recipe 期望一致。

### 方向 2（置信度: 低）
在 Dockerfile 的构建步骤中，于 `./scripts/install_deps.sh` 之前预先下载 bzip2 1.0.8 源码包并放入 Conan 本地缓存（`~/.conan/data/bzip2/1.0.8/_/_/source/`），绕过 Conan 的 `source()` 下载步骤（Conan 检测到源码已存在时会跳过下载）。

## 需要进一步确认的点
1. 该 `bzip2_source_fix.py` 钩子位于构建环境的哪个路径（宿主机全局 Conan hooks 目录或项目级配置），需要查看其当前尝试的 URL 列表，确定是哪个/哪些 URL 返回了 403。
2. 确认已有的 Milvus 2.6.0 SP2 Dockerfile 在当前时间点重新构建是否也会触发相同的 bzip2 403 错误——如果 SP2 也失败，则确认这是时间相关（upstream 源短期故障或永久变更）而非 SP4 特定问题。
3. 确认 Conan recipe 中 bzip2 1.0.8 期望的源码 hash（SHA256），以确保替换下载源后 hash 校验通过。
4. 排查是否需要将 Conan 或 pip 的整体镜像源改为内部/华为云等更稳定的镜像，而非针对单个包打补丁（`bzip2_source_fix.py` 的方式属于逐个包修补，可能持续出现类似问题）。

## 修复验证要求
若采用方向 1：code-fixer 必须找到构建环境中 `bzip2_source_fix.py` 的实际文件，确认当前配置的 URL 列表，替换为可从 CI 环境正常下载的镜像 URL。提交前必须验证新 URL 返回 HTTP 200 且下载文件 hash 与 Conan 期望一致。若采用方向 2：code-fixer 必须在 Dockerfile 中加入 bzip2 预下载步骤并验证 Conan 在 `source()` 阶段检测到已有缓存文件时确实跳过下载。
