# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: x86编译选项在ARM上不兼容
- 新模式症状关键词: unrecognized command-line option, -mavx, -msse4, -mpopcnt, -m64, aarch64, faiss

## 根因分析

### 直接错误
```
#9 106.4 g++ -fPIC -m64 -Wall -g -O3 -mavx -msse4 -mpopcnt -fopenmp -Wno-sign-compare -std=c++11 -fopenmp -c hamming.cpp -o hamming.o  
#9 106.4 g++: error: unrecognized command-line option '-m64'
#9 106.4 g++: error: unrecognized command-line option '-mavx'
#9 106.4 g++: error: unrecognized command-line option '-msse4'
#9 106.4 g++: error: unrecognized command-line option '-mpopcnt'
#9 106.4 make: *** [Makefile:43: hamming.o] Error 1
```

### 根因定位
- 失败位置: `/tmp/faiss/Makefile:43` → 实际根因在 `example_makefiles/makefile.inc.Linux`
- 失败原因: faiss 项目的 `example_makefiles/makefile.inc.Linux` 硬编码了 x86_64 专属的编译器选项（`-m64`、`-mavx`、`-msse4`、`-mpopcnt`），这些选项在 aarch64 架构的 g++ 上不被识别。CI 在 aarch64 构建节点上编译 faiss 源码时触发此错误。

### 与 PR 变更的关联

**存在严重不一致**：PR diff 中的 Dockerfile（共 21 行）使用 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}` 通过 conda 安装预编译包，不涉及任何源码编译。但 CI 日志显示构建的 Dockerfile 包含 `yum install -y gcc gcc-c++ make openblas-devel swig git && git clone ... && make && make py` 等从源码编译的步骤（共 25 行，报错位于 Dockerfile:19）。

这两种构建方式截然不同，说明 CI 实际运行的 Dockerfile 与 PR 提交的 Dockerfile 不一致。可能的原因包括：
- CI 流水线在构建前对 Dockerfile 进行了模板化生成/替换
- CI 运行了错误的 commit 或分支
- 日志中的 `Dockerfile:19` 指向了一个生成后的中间产物

无论原因为何，该 PR 新增的 `20180223-oe2403sp3` 构建目标声明支持 amd64 和 arm64 双架构（见 `image-info.yml` 和 `meta.yml`），而 CI 实际运行的 Dockerfile 在 aarch64 上编译 faiss 源码时因架构不兼容的编译选项而失败。

## 修复方向

### 方向 1（置信度: 中）
**若 CI 实际运行的是 conda 版本的 Dockerfile**（与 PR diff 一致）：需确认 `faiss-cpu=20180223` 在 pytorch/conda-forge channel 中是否存在。20180223 是五年前的版本号，conda-forge 可能从未发布过该版本，导致 conda install 失败后 CI 回退到源码编译。需验证 conda 包可用性，或改用其他安装方式。

### 方向 2（置信度: 中）
**若 CI 实际运行的是源码编译版本的 Dockerfile**（与 CI 日志一致）：需修改 `example_makefiles/makefile.inc.Linux` 中的编译选项，根据 `TARGETARCH` 区分 x86_64 和 aarch64，在 aarch64 上移除 `-m64`、`-mavx`、`-msse4`、`-mpopcnt` 等 x86 专属 flag。可在 `cp makefile.inc` 后用 `sed` 条件性去除这些选项。

### 方向 3（置信度: 低）
CI 流水线配置问题，导致 PR 提交的 Dockerfile 未被正确使用。需检查 CI 流程中的 Dockerfile 生成/覆盖逻辑。

## 需要进一步确认的点
1. **PR diff 与 CI 日志中的 Dockerfile 内容完全不一致**：diff 显示 conda 安装（21行），CI 日志显示源码编译（25行）。需确认 CI 流水线是否存在 Dockerfile 模板生成步骤，以及该模板是否覆盖了 PR 提交的内容。
2. 需确认 `faiss-cpu=20180223` 在 conda-forge/pytorch channel 是否真实存在。该版本号对应 2018 年 2 月 23 日，极可能不在任何 conda channel 中。
3. 需获取 CI 流水线中实际使用的 Dockerfile 完整内容，确认是流水线生成产物还是 PR 提交的原始文件。
4. 需确认该 CI 失败是仅在 aarch64 架构上出现，还是 amd64 也失败（日志只显示了 aarch64 构建过程）。
