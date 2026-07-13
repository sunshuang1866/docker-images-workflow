# CI 失败分析报告

## 基本信息
- PR: #2998 — chore(cp2k): add openEuler 24.03-LTS-SP4 support
- 失败类型: timeout
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建耗时超时
- 新模式症状关键词: Build was aborted, Aborted by, install_cp2k_toolchain.sh, --install-all, SIRIUS

## 根因分析

### 直接错误
```
#11 6034.9 Installing from scratch into /opt/cp2k/tools/toolchain/install/sirius-7.7.0
#11 6035.6 patching file src/core/memory.hpp
Build was aborted
Aborted by 闫志聪
Notifying upstream projects of job completion
Finished: ABORTED
```

### 根因定位
- 失败位置: `HPC/cp2k/2025.2/24.03-lts-sp4/Dockerfile`:17-26（toolchain 安装步骤）
- 失败原因: `install_cp2k_toolchain.sh --install-all` 从源码编译了 25+ 个工具链库（含 OpenMPI、OpenBLAS、LIBINT、LIBXC、ELPA、PLUMED、hdf5、SIRIUS 等），其中 LIBINT 耗时 ~33 分钟、LIBXC 耗时 ~16.5 分钟、OpenMPI 耗时 ~14 分钟、OpenBLAS 耗时 ~13 分钟。截至被中止时仅 toolchain 安装步骤已运行约 100 分钟，尚未进入 cp2k 主体编译（`make ARCH=local VERSION=psmp`），构建被手动中止，推测超出了 CI 流水线的最大允许执行时间。

### 与 PR 变更的关联
PR 新增了 cp2k 2025.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，使用了 `--install-all` 参数从源码全量编译所有依赖。该 Dockerfile 的构建时间远超出 CI 流水线的时间上限，导致构建被中止。这不是代码逻辑错误，而是构建时间过长引发的基础设施限制问题。

## 修复方向

### 方向 1（置信度: 中）
将 `--install-all` 替换为按需安装，只保留 cp2k psmp 构建真正需要的库。例如，若目标场景不需要 SIRIUS、PLUMED、ELPA、libsmeagol 等库，可移除对应选项，大幅缩短 toolchain 安装时间。需确认 cp2k 2025.2 版本 `install_cp2k_toolchain.sh` 支持哪些 `--with-<lib>=install` 选项，以及哪些库是 psmp 构建的必要依赖。

### 方向 2（置信度: 中）
利用已存在的 cp2k 2025.2 SP2（`HPC/cp2k/2025.2/24.03-lts-sp2/Dockerfile`）作为参考，检查其是否采用了更精简的 toolchain 安装策略（如非 `--install-all`），将相同的优化策略应用到 SP4 版本。

### 方向 3（置信度: 低）
如果 CI 平台允许为 cp2k 类重构建镜像单独配置更长的超时时间，可申请延长该 job 的超时限制。但考虑到 toolchain 安装已在 100 分钟时仅到 SIRIUS（约第 23/25 个库），后续还有 cp2k 主体编译（通常也需数十分钟），即便延长也可能不够，此方向仅作为辅助手段。

## 需要进一步确认的点
1. 该 CI 流水线的最大超时时间是多少？需要确认中止是由超时触发还是人工主动中止。
2. `HPC/cp2k/2025.2/24.03-lts-sp2/Dockerfile`（同版本不同 OS）的 toolchain 安装策略是否与 SP4 一致？若 SP2 能成功构建，其差异点可作为优化参考。
3. cp2k 2025.2 `install_cp2k_toolchain.sh` 的帮助信息（`./install_cp2k_toolchain.sh --help`）中支持哪些独立库的 `--with-<lib>=install` 选项，以评估哪些库可以裁剪。
4. 目标镜像的使用场景是否确实需要所有 toolchain 库？若仅需核心计算能力，可裁剪 SIRIUS、PLUMED、libsmeagol、libvori、GreenX 等非核心库。
