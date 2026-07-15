# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: C++构建失败(日志缺省)
- 新模式症状关键词: exit code: 8, make build-cpp, CXXFLAGS

## 根因分析

### 直接错误

```
#13 ERROR: process "/bin/sh -c git clone -b v2.6.0 https://github.com/milvus-io/milvus.git &&     cd milvus/ &&     conan config set tools.files.download:download_cache=/root/.conan/download_cache &&     wget -q https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz -O /tmp/bzip2-1.0.8.tar.gz &&     mkdir -p /root/.conan/download_cache &&     cp /tmp/bzip2-1.0.8.tar.gz /root/.conan/download_cache/7df308b2324eeb3da2c515674ac57ffb71ae1ce0f2c97e1483bad1f7e83092a7 &&     cp /tmp/bzip2-1.0.8.tar.gz /root/.conan/download_cache/1c430c86032c4caf707eb8c6cce771b3cdce171f6bc9531a63dae0f1a434f8d2 &&     cp /tmp/bzip2-1.0.8.tar.gz /root/.conan/download_cache/f542843c78e20fc955e391c32ae868dd097712a466148baf93313784b5fbec1d &&     rm -f /tmp/bzip2-1.0.8.tar.gz &&     CXXFLAGS=\"-I/usr/include/openblas\" make build-cpp &&     make build-go" did not complete successfully: exit code: 8
ERROR: failed to solve: process "..." did not complete successfully: exit code: 8
```

Git clone 成功完成（checkout 到 `4def0255a928287f982f1d6b8c53ed32127bb84d`），但后续 `make build-cpp` 返回退出码 8，导致整个 RUN 命令失败。`&&` 链式结构下 `make build-go` 未被执行。

### 根因定位
- 失败位置: `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile:23-33`（builder 阶段第 4 个 RUN 指令中的 `make build-cpp`）
- 失败原因: `make build-cpp`（Milvus C++ 组件构建）以退出码 8 失败。**关键问题——CI 日志中缺失 `make build-cpp` 的实际编译错误输出**。日志仅包含 git clone 的成功输出和 Docker 层级的最终错误摘要，`make build-cpp` 内部的编译器报错信息（具体哪个源文件、哪一行、什么错误）完全不可见。

### 与 PR 变更的关联

PR 变更新增了 `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`，基于 `openeuler/openeuler:24.03-lts-sp4` 基础镜像构建 Milvus 2.6.0。

**注意——CI 实际执行的 RUN 命令与 PR diff 中的 Dockerfile 不一致**：
- **PR diff 中的 RUN 命令**：`git clone ... && ./scripts/install_deps.sh && CXXFLAGS="-I/usr/include/openblas" make build-cpp && make build-go`
- **CI 日志中实际执行的 RUN 命令**：`git clone ... && conan config set ... && wget bzip2 ... && cp bzip2 ... && CXXFLAGS="-I/usr/include/openblas" make build-cpp && make build-go`

CI 构建系统将 `./scripts/install_deps.sh` 替换为手动配置 conan 下载缓存和预下载 bzip2 的步骤。此替换逻辑与 PR 的新增 Dockerfile 不直接相关，但替换后整个 RUN 步骤与原始意图不同。

**失败与 PR 的关联**：无法确定。`make build-cpp` 的失败可能是 openEuler 24.03-LTS-SP4 平台特有的编译问题（如 GCC 版本差异、系统库 ABI 变化、缺少特定的 -devel 包），也可能与 CI 注入的 RUN 命令改造有关（`./scripts/install_deps.sh` 被移除后缺少某些依赖安装步骤）。

## 修复方向

### 方向 1（置信度: 低）
获取 `make build-cpp` 的完整编译输出后，根据具体错误类型修复：
- 若为缺少头文件/库：在 `yum install` 中补充对应的 `-devel` 包（参照历史模式10）
- 若为编译器版本不兼容（如 GCC 的新版本报告之前未报告的 warning-as-error）：添加编译标志或 patch 上游源码
- 若为 openBLAS 相关符号未定义：调整 `CXXFLAGS` 或 openBLAS 版本

### 方向 2（置信度: 低）
若 CI 注入的 RUN 命令改造（移除 `./scripts/install_deps.sh` 并手动配置 conan/bzip2）是导致构建失败的原因——即 `install_deps.sh` 原本会安装某些 `make build-cpp` 所需的依赖，但被移除后这些依赖缺失——则需要在 Dockerfile 中显式补充缺失的依赖包，或确保 `install_deps.sh` 的等价依赖全部被保留。

## 需要进一步确认的点

1. **最关键——获取 `make build-cpp` 的完整编译输出**：当前 CI 日志中缺失 Milvus C++ 构建阶段的实际错误信息。需要从 Jenkins 构建日志的原始输出中提取 `make build-cpp` 阶段的编译器报错（可能在 Docker build 输出中被截断或未采集）。没有这条信息，无法精确定位根因。

2. **确认 CI 系统是否对 Dockerfile 进行了 RUN 命令改造**：CI 日志中实际执行的 RUN 命令与 PR diff 中的 Dockerfile 不一致（`./scripts/install_deps.sh` 被替换为 conan/bzip2 手动步骤）。需确认这是 CI 系统的通用行为还是偶发异常，以及改造是否可能遗漏了必要的依赖安装。

3. **对比同版本在 openEuler 24.03-LTS-SP2 上的构建**：`Database/milvus/2.6.0/24.03-lts-sp2/Dockerfile` 使用相同的 Milvus 2.6.0 版本和基本一致的构建步骤。如果 SP2 构建成功而 SP4 失败，差异集中在基础镜像版本差异（GCC、glibc、系统库版本等）。

4. **验证 openEuler 24.03-LTS-SP4 的 `openblas-devel` 包**：Dockerfile 使用 `CXXFLAGS="-I/usr/include/openblas"`，需确认 SP4 中 openBLAS 头文件和库文件的路径、版本与 SP2 是否一致。

## 修复验证要求

由于实际编译错误输出缺失，任何修复在提交前必须：
1. 触发一次完整的 CI 构建，确认 `make build-cpp` 能完整通过
2. 若修复涉及更改 `yum install` 包列表，需确认新增包在 openEuler 24.03-LTS-SP4 仓库中确实可用（通过 `yum list` 或 `dnf search` 验证）
3. 若修复涉及调整 `CXXFLAGS` 或编译选项，需确保最终构建的二进制文件能正常链接和运行
