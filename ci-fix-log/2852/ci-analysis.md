# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Conan bzip2 源 403
- 新模式症状关键词: bzip2/1.0.8, AuthenticationException, 403: Forbidden, conan install failed, bzip2_source_fix.py

## 根因分析

### 直接错误
```
#14 626.0 [HOOK - bzip2_source_fix.py] pre_source(): Patched bzip2/1.0.8 source URLs to use working mirrors
#14 626.0 bzip2/1.0.8: Configuring sources in /root/.conan/data/bzip2/1.0.8/_/_/source/src
#14 626.8 ERROR: bzip2/1.0.8: Error in source() method, line 50
#14 626.8 	get(self, **self.conan_data["sources"][self.version], strip_root=True)
#14 626.8 	AuthenticationException: 403: Forbidden
#14 626.9 conan install failed
#14 626.9 make: *** [Makefile:263: build-3rdparty] Error 1
#14 ERROR: process "/bin/sh -c git clone -b v${VERSION} https://github.com/milvus-io/milvus.git && ... make build-cpp && make build-go" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:47-51`（`RUN git clone ... make build-cpp` 步骤）
- 失败原因: Milvus 2.6.0 的 `./scripts/install_deps.sh` 内部通过 conan 包管理器安装第三方依赖，conan 在下载 `bzip2/1.0.8` 源码时，已通过 `bzip2_source_fix.py` hook 将 URL 重定向到备用镜像，但所有镜像（原始源和 patched 后的镜像）均返回 HTTP 403 Forbidden，导致 conan install 失败，进而 `make build-cpp` 中断。

### 与 PR 变更的关联
**部分关联**。PR 新增了整个 Dockerfile，引入了首次在 openEuler 24.03-LTS-SP4 上构建 Milvus 2.6.0 的完整流程。失败环节 `./scripts/install_deps.sh` 来自上游 Milvus 源码，其中的 `bzip2_source_fix.py` hook 也是项目自带的修复脚本，**不随本次 PR 变更**。但 PR 的 Dockerfile 触发该流程在 CI 环境中首次执行，暴露了当前 CI 网络环境下 bzip2 1.0.8 所有可用镜像源均不可达（403）的问题。

## 修复方向

### 方向 1（置信度: 中）
更新 Milvus 源码中 `bzip2_source_fix.py` hook 的镜像列表，将 bzip2 1.0.8 的下载源替换为 CI 环境可访问的镜像（如 `repo.huaweicloud.com` 或 `sourceforge.net` 的直接链接）。该 hook 通常在 Milvus 源码中的 `./scripts/install_deps.sh` 或 conan hooks 目录下，需要在 Dockerfile 中通过 `sed`/`python` 在 `install_deps.sh` 执行前 patch 该 hook 中的 URL 列表，或在 `make build-cpp` 前设置 conan 环境变量指定自定义 mirror。

### 方向 2（置信度: 低）
如果确认是 CI runner 网络出口 IP 被目标镜像站封禁（类似模式04），且该问题仅影响特定 CI runner 节点，则此为 infra-error，需排查 CI 网络配置而非修改 Dockerfile。

## 需要进一步确认的点
1. 需要确认项目中已有的 `bzip2_source_fix.py` hook 具体 patch 了哪些镜像 URL，判断是否存在已知可用但未列入的镜像源。
2. 需要确认 CI 构建节点的网络环境：能否直接访问 `sourceware.org/pub/bzip2/` 或 `https://sourceforge.net/projects/bzip2/`。
3. 需要确认 Milvus 2.6.0 源码中 `./scripts/install_deps.sh` 的具体路径和 conan hooks 的注册方式，以便确定 patch 的注入位置。
4. 若最终确认属于 infra-error（网络问题），则标记为无需代码修复。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
若采用方向1，修复需要在 Dockerfile 中通过 `sed` 或 Python 脚本修改 `bzip2_source_fix.py` 中的镜像 URL 列表。code-fixer 在提交前必须：
1. 从 Milvus 2.6.0 源码（`v2.6.0` tag）获取 `bzip2_source_fix.py` 的实际内容，确认待修改的 URL 行号和上下文。
2. 验证新替换的镜像 URL 在 CI 环境中确实可访问（HTTP 200），确保正则/sed 匹配后不会引入无效 URL。
