# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式（近似于模式04）
- 新模式标题: 预下载绕过镜像hook致403
- 新模式症状关键词: curl: (22), 403, sourceware.org, bzip2, Conan hook, pre-download

## 根因分析

### 直接错误

```
#13 [builder 4/5] RUN mkdir -p /root/.conan/downloads/ab && \
    curl -fsSL --retry 3 --retry-delay 5 \
      -o /root/.conan/downloads/ab/ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269 \
      https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz
#13 3.298 curl: (22) The requested URL returned error: 403
#13 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 22
------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 22
```

### 根因定位
- 失败位置: Dockerfile builder 阶段第 4/5 步（对应日志 step #13），Dockerfile:43-46
- 失败原因: CI 构建流程在 Conan 构建前执行 bzip2 预下载步骤，直接访问 `sourceware.org` 下载 bzip2-1.0.8.tar.gz，该站点返回 HTTP 403。而 step #12 中已设置了 Conan hook（`bzip2_source_fix.py`）将 bzip2 源 URL 从 `sourceware.org` 替换为 `mirrors.kernel.org`，但 step #13 的预下载绕过了此 hook，直接使用原始且已不可用的 URL。

### 与 PR 变更的关联
PR 仅为 milvus 2.6.0 新增了 openEuler 24.03-LTS-SP4 的支持 Dockerfile（53 行）。PR diff 中 Dockerfile 的 builder 阶段仅包含 3 个 RUN 指令：
1. `yum install` + Go 安装
2. `rustup` + `pip install conan==1.61.0`
3. `git clone milvus` + `scripts/install_deps.sh` + `make build-cpp` + `make build-go`

但 CI 日志显示实际构建的 Dockerfile 在 step #12 和 #13 中包含了额外的 hook 设置与 bzip2 预下载逻辑，这些内容不在 PR diff 范围内。失败的 step #13（bzip2 预下载）是由 CI 构建编排层注入的步骤，非 PR 作者直接提交。该步骤与 step #12 中设置的 Conan hook 存在逻辑矛盾——hook 已正确将 bzip2 URL 替换为镜像源，但预下载步骤却绕过了它。

## 修复方向

### 方向 1（置信度: 高）
将 step #13 中 bzip2 预下载的源 URL 与 step #12 Conan hook 中的替换目标保持一致，即将 `https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz` 改为 `https://mirrors.kernel.org/sourceware/bzip2/bzip2-1.0.8.tar.gz`（该镜像源在 step #12 中已验证为可用的替代源），使预下载与 hook 逻辑一致。

### 方向 2（置信度: 中）
移除 step #13 的 bzip2 预下载步骤，依赖 step #12 中设置的 Conan hook 在 Conan 构建阶段自动从镜像源下载 bzip2。预下载本身是对 Conan 下载缓存的预热，如果 Conan hook 能正确工作，预下载为冗余步骤。

### 方向 3（置信度: 低）
将预下载步骤移入 Conan hook 内部（在 `bzip2_source_fix.py` 中完成），或将 URL 改用对 CI 环境更友好的镜像站（如 `mirrors.tuna.tsinghua.edu.cn` 等）进行预下载。

## 需要进一步确认的点
1. Step #12 和 #13 中的额外构建步骤（bzip2 hook 设置和预下载）是由哪个 CI 编排层注入的？需要确认注入机制（如 `euler_builder` 的 Dockerfile 预处理逻辑），以便准确定位应在何处修改源 URL。
2. `mirrors.kernel.org/sourceware/bzip2/bzip2-1.0.8.tar.gz` 在 CI 构建环境中的网络可达性是否已通过验证。
3. PR diff 中的 Dockerfile 是否被后续提交/amend 更新过（当前 diff 与 CI 构建的 Dockerfile 可能不一致）。
4. 预下载的目标 SHA256（`ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`）是否与 `mirrors.kernel.org` 上的 bzip2-1.0.8.tar.gz 实际 hash 一致——若镜像站文件有差异，需要同时更新 hash 值。

## 修复验证要求
若修复方向 1 被采用，code-fixer 必须在提交前：
1. 确认 `https://mirrors.kernel.org/sourceware/bzip2/bzip2-1.0.8.tar.gz` 在 CI runner 网络环境中可达且返回 HTTP 200
2. 验证下载文件的 SHA256 与预下载步骤中硬编码的 hash（`ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`）一致
3. 确认 `./scripts/install_deps.sh` 在依赖安装过程中不会重复触发同一个 sourceware.org 下载而导致二次失败
