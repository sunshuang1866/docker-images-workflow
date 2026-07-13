# 修复摘要

## 修复的问题
`install_cp2k_toolchain.sh --install-all` 从源码编译 25+ 个工具链库导致构建超时。

## 修改的文件
- `HPC/cp2k/2025.2/24.03-lts-sp4/Dockerfile`: 在 `--install-all` 之后追加 `--with-<lib>=no` 选项，禁用非核心库的编译安装，保留 psmp 构建必需的依赖。

## 修复逻辑
根据分析报告方向 1（置信度: 中），`--install-all` 编译了包括 SIRIUS、ELPA、PLUMED、libvori、COSMA、libsmeagol 等在内的全部库，仅 toolchain 安装阶段已超 100 分钟。修复保留了 psmp 构建的核心依赖（openmpi、openblas、fftw、libint、libxc、libgrpp、libxsmm、scalapack、dbcsr、cmake），显式禁用非必要库：

已从上游 `support/v2025.2` 获取 `install_cp2k_toolchain.sh` 验证：
- `--install-all` 将全部包的 `with_*` 设为 `__INSTALL__`，后续 `--with-<lib>=no` 可覆盖为 `__DONTUSE__`
- `--with-sirius=no` 自动触发 `elif` 分支将 `pugixml` 设为 `__DONTUSE__`
- SIRIUS 的级联依赖（spfft、spla、gsl、spglib、hdf5、libvdwxc、cosma）在 `--install-all` 下已为 `__INSTALL__`，`--with-sirius=no` 不会自动禁用它们，因此显式传递 `--with-xxx=no` 逐个禁用

禁用的库及其级联依赖共计约 17 个包，预计可节省 45-65 分钟编译时间，使构建回到 CI 时间限制之内。

## 潜在风险
- 禁用的库（ELPA、SIRIUS、PLUMED 等）对应的 CP2K 功能将不可用。若目标镜像需使用这些功能（如大体系特征值求解、增强采样、平面波计算），需重新启用对应库。当前禁用集面向通用 cp2k psmp 基础能力。