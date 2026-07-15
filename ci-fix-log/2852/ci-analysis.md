# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Conan bzip2下载源403
- 新模式症状关键词: bzip2, 403 Forbidden, conan install, bzip2_source_fix.py, build-3rdparty, AuthenticationException

## 根因分析

### 直接错误
```
#13 320.8 [HOOK - bzip2_source_fix.py] pre_source(): Patched bzip2/1.0.8 source URLs to use working mirrors
#13 320.8 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#13 322.7 ERROR: bzip2/1.0.8: Error in source() method, line 50
#13 322.7 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#13 322.7 	AuthenticationException: 403: Forbidden
#13 322.7 conan install failed
#13 322.7 make: *** [Makefile:263: build-3rdparty] Error 1
#13 ERROR: process "/bin/sh -c git clone ... && cd milvus/ && ./scripts/install_deps.sh && ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: Dockerfile:42-46（`RUN git clone -b v2.6.0 ... make build-cpp` 步骤内的 `make build-3rdparty` 中的 `conan install`）
- 失败原因: Milvus 构建过程中，Conan 包管理器尝试下载依赖 `bzip2/1.0.8` 的源码包，Conan 社区钩子 `bzip2_source_fix.py` 虽然成功将下载 URL 替换为镜像源，但镜像源同样返回 HTTP 403 Forbidden，导致 Conan 依赖下载失败，`make build-3rdparty` 目标构建中断。

### 与 PR 变更的关联
- **PR 变更本身不包含导致此失败的逻辑缺陷**。Dockerfile 的构建步骤（`git clone`、`./scripts/install_deps.sh`、`make build-cpp`）与已有的 SP2 版本 Dockerfile 构造一致，属于 Milvus 官方构建流程。
- 失败的直接原因是 Conan 从外部源下载 bzip2/1.0.8 源码时遭遇 403，这是一个外部依赖可用性问题，而非 Dockerfile 编写错误。
- 但由于该 Dockerfile 是新提交的，当前 CI 为该新镜像首次运行构建，触发了此问题。已有的 SP2 Dockerfile 如果此时重建，理论上也会遇到同样的 bzip2 下载 403 问题。

## 修复方向

### 方向 1（置信度: 中）
Conan 社区钩子 `bzip2_source_fix.py` 指向的备用镜像源不可用（403），需要更新该钩子或用其他方式提供 bzip2/1.0.8 源码。在 Dockerfile 的构建步骤中，在 `./scripts/install_deps.sh` 之前，手动将 bzip2/1.0.8 的源码（`.tar.gz`）下载到 Conan 的本地缓存目录（`~/.conan/data/bzip2/1.0.8/_/_/source/`），绕过 Conan 的网络下载环节。可从其他可访问的源（如 `sourceware.org/pub/bzip2/`、`repo.huaweicloud.com` 等）预先下载 bzip2-1.0.8.tar.gz。

### 方向 2（置信度: 低）
在 `./scripts/install_deps.sh` 调用前，设置 Conan 环境变量 `CONAN_HOOKS` 禁用全局钩子，然后用 Conan 配置命令将 bzip2 的下载源指向经测试可用的镜像。但日志中钩子已尝试替换 URL 仍失败，说明当前钩子内置的镜像列表全部不可用，此方向需要同时更新钩子文件。

## 需要进一步确认的点
1. 确认 `bzip2_source_fix.py` 钩子实际替换后的 URL 是什么（日志未显示具体替换后的 URL），以判断是短期网络波动还是镜像永久失效。
2. 验证已有 Milvus 2.6.0 SP2 Dockerfile 在当前时间点构建是否也会遇到同样的 bzip2 403 错误，以排除 CI runner 网络策略变更的可能性。
3. 确认 CI 构建环境中是否有网络代理或防火墙导致对特定域名的 HTTP 请求被拦截返回 403。
4. 检查 `https://www.sourceware.org/git/?p=bzip2.git` 等 bzip2 上游源在 CI runner 环境中的可达性。

## 修复验证要求
若修复采用"手动预下载 bzip2 到 Conan 缓存目录"的方向，code-fixer 必须在 CI 环境中验证所选用的 bzip2 下载源确实可达（使用 `wget --spider` 或 `curl -I` 确认返回 200），而非仅依赖文档或历史记录中的 URL。
