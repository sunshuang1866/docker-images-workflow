# CI 失败分析报告

## 基本信息
- PR: #2852 — chore(milvus): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游脚本OS不兼容
- 新模式症状关键词: `Unable to find a match, epel-release, centos-release-scl-rh, devtoolset, scl_source, install_deps.sh, openEuler`

## 根因分析

### 直接错误
```
#13 206.0 No match for argument: epel-release
#13 206.0 No match for argument: centos-release-scl-rh
#13 206.0 Error: Unable to find a match: epel-release centos-release-scl-rh
#13 206.3 No match for argument: devtoolset-11-gcc
#13 206.3 No match for argument: devtoolset-11-gcc-c++
#13 206.3 No match for argument: devtoolset-11-gcc-gfortran
#13 206.3 No match for argument: devtoolset-11-libatomic-devel
#13 206.3 No match for argument: llvm-toolset-11.0-clang
#13 206.3 No match for argument: llvm-toolset-11.0-clang-tools-extra
#13 206.3 No match for argument: lcov
#13 206.3 Error: Unable to find a match: devtoolset-11-gcc devtoolset-11-gcc-c++ devtoolset-11-gcc-gfortran devtoolset-11-libatomic-devel llvm-toolset-11.0-clang llvm-toolset-11.0-clang-tools-extra lcov
#13 209.1 /etc/profile.d/llvm-toolset-11.sh: line 1: scl_source: No such file or directory
#13 ERROR: process "/bin/sh -c ... ./scripts/install_deps.sh && ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: Dockerfile 第 22 行，RUN 指令中执行的 `./scripts/install_deps.sh`
- 失败原因: Milvus 2.6.0 上游项目的 `./scripts/install_deps.sh` 脚本针对 CentOS/RHEL 操作系统设计，脚本内通过 yum/dnf 尝试安装 CentOS 专有的 SCL（Software Collections）仓库包（`epel-release`、`centos-release-scl-rh`、`devtoolset-11-*`、`llvm-toolset-11.0-*`）以及 `lcov` 包，这些包在 openEuler 24.03-LTS-SP4 的仓库中均不存在，导致 yum 包查询失败。此外脚本还试执行 `source scl_source enable devtoolset-11` 等命令，但 `scl_source` 命令在 openEuler 上亦不可用。虽然脚本在个别包安装失败后仍继续执行后续步骤（pip 安装 conan、rust 工具链更新），但最终累积了非零退出码（exit code 8），导致 RUN 指令的 `&&` 链中断，构建失败。

### 与 PR 变更的关联
PR 新增的 `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile` 第 22-24 行无条件调用 `./scripts/install_deps.sh`。该脚本来自 Milvus 上游仓库（`github.com/milvus-io/milvus` 的 `v2.6.0` tag），并非 openEuler 社区维护，其内部硬编码了对 CentOS/RHEL 包管理体系的依赖，无法在 openEuler 24.03-LTS-SP4 上正确执行。PR 的其他变更（README.md、image-info.yml、meta.yml）均为元数据更新，与此失败无关。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中不直接调用上游的 `./scripts/install_deps.sh`，改为手动安装 openEuler 上可用的等效依赖包。需要：
1. 移除 RUN 指令中的 `./scripts/install_deps.sh` 调用
2. 分析 `install_deps.sh` 中各个安装步骤的实际目的（gcc/g++ 工具链、LLVM/clang 工具链、cmake、rust、conan、lcov 等），在 openEuler 仓库中寻找对应的包或替代方案
3. 对 openEuler 24.03-LTS-SP4 上无法替代的依赖（如 `lcov`），评估是否可跳过或从源码编译

### 方向 2（置信度: 中）
保留 `./scripts/install_deps.sh` 调用，但在此之前通过 `sed`/`patch` 修改该脚本，移除其中对 CentOS/RHEL 专属包（`epel-release`、`centos-release-scl-rh`、`devtoolset-11-*`、`llvm-toolset-11.0-*`）的安装指令，并将 `scl_source` 调用替换为空操作或等效的 openEuler 命令。此方向需要深入理解上游脚本的完整逻辑，确保 patch 后不会遗漏关键依赖。

## 需要进一步确认的点
1. Milvus 2.6.0 上游 `install_deps.sh` 脚本的完整内容，确认所有被安装的包及其在 openEuler 上的可用性
2. 已有的 `Database/milvus/2.6.0/24.03-lts-sp2/Dockerfile` 是如何处理同一问题的——该镜像已在 24.03-LTS-SP2 上构建成功，可以参考其依赖安装策略
3. `lcov` 包在 openEuler 24.03-LTS-SP4 上的替代方案（如 `gcov` 或从源码编译），或确认构建流程是否可跳过代码覆盖率工具
4. CI 系统是否对 Dockerfile 注入了额外的 RUN 步骤（日志中出现了 PR diff 中不存在的 `conan config set`、`bzip2` 预缓存等步骤），需确认 PR 实际提交的 Dockerfile 与 CI 构建时使用的 Dockerfile 是否一致

## 修复验证要求
1. 修改后的 Dockerfile 需在 CI 环境中重新构建验证（`docker build` 完整流程通过）
2. 若采用方向 2（patch install_deps.sh），必须从 `https://github.com/milvus-io/milvus/raw/v2.6.0/scripts/install_deps.sh` 获取原始脚本内容，确保 sed/patch 正则能正确匹配目标行
3. 同步验证构建产物 `lib64/`、`lib/`、`bin/` 目录下的文件是否被正确 COPY 到最终镜像，确保 Milvus 运行时功能正常
