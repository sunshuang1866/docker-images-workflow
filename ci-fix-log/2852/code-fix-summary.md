# 修复摘要

## 修复的问题
将 SP4 Dockerfile 构建阶段的 RUN 命令中的手动 conan/bzip2 预配置步骤恢复为 `./scripts/install_deps.sh`，与已验证可工作的 SP2 Dockerfile 保持一致。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 行 23-27 — 将手动 `conan config set` + `wget bzip2` + `cp` 等多个步骤替换为单行 `./scripts/install_deps.sh`，对齐 SP2 的构建方式。

## 修复逻辑

**根因对应分析报告中的方向2**：CI 系统会将 `./scripts/install_deps.sh` 替换为标准化的 conan/bzip2 缓存预配置步骤。SP2 Dockerfile 中使用了 `./scripts/install_deps.sh`，CI 系统自动对其进行标准化替换后构建成功。SP4 Dockerfile 中直接写入了手动 conan/bzip2 预配置步骤（而非 `./scripts/install_deps.sh`），导致 CI 替换逻辑可能未被触发或生成不同的 RUN 命令，`make build-cpp` 因此失败。

修复后 SP4 的 RUN 命令结构与 SP2 完全一致，CI 系统将对两者应用相同的标准化转换，确保构建流程一致。

**关于 `install_deps.sh` 的验证**：已从上游 `https://raw.githubusercontent.com/milvus-io/milvus/v2.6.0/scripts/install_deps.sh` 获取源文件。该脚本在 yum 系 Linux 上会尝试安装 `epel-release centos-release-scl-rh devtoolset-11-*` 等 CentOS 专用包，无法直接在 openEuler 上运行。CI 系统之所以能对 SP2 构建成功，正是因为其自动将 `./scripts/install_deps.sh` 替换为 conan/bzip2 手工步骤。本次修复确保 SP4 使用与 SP2 相同的 `./scripts/install_deps.sh` 调用方式，从而利用 CI 系统的同一套替换逻辑。

## 潜在风险
- 如果 CI 系统并未对所有 Milvus Dockerfile 自动替换 `install_deps.sh`（仅对特定 base image 匹配），则 `install_deps.sh` 会因无法安装 CentOS 专用包而失败，报错会从 `make build-cpp exit code 8` 变为 `yum install centos-release-scl-rh` 失败。这种情况下需要进一步排查 CI 替换机制的触发条件。
- 由于 CI 日志中缺失 `make build-cpp` 的实际编译错误输出，无法 100% 确认真实根因是否为 RUN 命令差异。若此修复仍未通过，说明根因在于 openEuler 24.03-LTS-SP4 基础镜像本身的编译器/库版本问题，需获取完整编译输出后进一步诊断。