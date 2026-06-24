# 修复摘要

## 修复的问题
VTK 全核并行编译时单个 C++ 模板文件（vtkArrayBulkInstantiate_*.cxx）内存消耗过大，触发 OOM Killer 导致 `cc1plus` 被 kill。

## 修改的文件
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/build-Slicer.sh`: 限制 cmake `--parallel` 为物理核心数的一半（核心数 ≤4 时保持原值）
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/build-CTKAppLauncher.sh`: 同上，预防性修复
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/build-tbb.sh`: 同上，预防性修复

## 修复逻辑
三个构建脚本均使用 `NUMBER_OF_PHYSICAL_CORES=$(grep -c ^processor /proc/cpuinfo)` 获取全部 CPU 核心数，然后以 `--parallel $NUMBER_OF_PHYSICAL_CORES` 进行全核并行编译。Slicer 的 SuperBuild 子项目 VTK 中包含大量模板实例化文件（如 `vtkArrayBulkInstantiate_char.cxx`、`vtkArrayBulkInstantiate_float.cxx`），单文件编译内存消耗极大，全核并行导致 CI runner 内存耗尽。

修复方案：在每个构建脚本中增加 `PARALLEL_JOBS=$(( NUMBER_OF_PHYSICAL_CORES > 4 ? NUMBER_OF_PHYSICAL_CORES / 2 : NUMBER_OF_PHYSICAL_CORES ))`，将 `--parallel` 的并行度限制为物理核心数的一半。当核心数 ≤ 4 时保持全核编译，确保低配环境不受影响。这对应分析报告中的修复方向 1（置信度: 高）。

## 潜在风险
- 降半核编译会增加构建时间（预计增加 30-60%），可能触发 CI 超时。若发生超时，需进一步评估是否在 cmake 配置阶段关闭不必要的 VTK 模块以减少编译单元数量。
- CTKAppLauncher 和 tbb 项目规模较小，原本未触发 OOM，降并行度对其影响有限。