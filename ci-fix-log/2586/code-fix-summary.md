# 修复摘要

## 修复的问题
CI 构建失败系基础设施错误（infra-error），CI 流水线实际运行了与 PR 提交内容不一致的 Dockerfile（源码编译版本），而非 PR 中的 conda 安装版本，无需修改 PR 源文件。

## 修改的文件
无代码修改。

## 修复逻辑
1. **Dockerfile 不一致**：PR diff 中的 Dockerfile（21 行）使用 `conda install -y -c pytorch -c conda-forge faiss-cpu=${VERSION}` 进行二进制安装，已通过 `TARGETARCH` 正确区分 arm64/amd64 架构下载对应的 Miniconda。该模式与已通过 CI 的 `1.14.1` 版本的 Dockerfile 完全一致。
2. **CI 实际运行内容**：CI 日志显示构建的 Dockerfile 包含 `yum install -y gcc gcc-c++ make openblas-devel swig git && git clone ... && make && make py` 的源码编译步骤（约 25 行），其中 `makefile.inc.Linux` 硬编码了 `-m64 -mavx -msse4 -mpopcnt` 等 x86_64 专属编译选项，在 aarch64 构建节点上触发 `unrecognized command-line option` 错误。
3. **根因判断**：PR 提交的 Dockerfile 本身不存在 x86 编译选项问题，CI 流水线使用了来源不明的另一个 Dockerfile 进行构建。因此属于 CI 基础设施/流水线配置问题，而非代码问题。

## 潜在风险
- CI 流水线恢复正常使用 PR 实际 Dockerfile 后，需验证 `faiss-cpu=20180223` 在 conda-forge/pytorch channel 中是否真实存在。该版本号对应 2018 年 2 月 23 日，conda channel 可能从未发布过此版本，届时 conda install 可能因找不到包而失败。
- 若 conda 包不可用，需考虑改用 pip 安装（`pip install faiss-cpu==1.7.4` 接近该时间点版本）或从源码编译（需正确区分 arm64/x86_64 编译选项）。