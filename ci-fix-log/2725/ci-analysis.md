# CI 失败分析报告

## 基本信息
- PR: #2725 — 【自动升级】3dslicer容器镜像升级至5.12.0版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 编译器OOM被杀
- 新模式症状关键词: `Killed signal terminated program cc1plus`, `c++: fatal error`, `vtkArrayBulkInstantiate`, OOM

## 根因分析

### 直接错误
```
#16 882.4 c++: fatal error: Killed signal terminated program cc1plus
#16 882.4 compilation terminated.
#16 882.4 gmake[5]: *** [Common/Core/CMakeFiles/CommonCore-objects.dir/build.make:328: Common/Core/CMakeFiles/CommonCore-objects.dir/vtkArrayBulkInstantiate_char.cxx.o] Error 1
#16 950.4 c++: fatal error: Killed signal terminated program cc1plus
#16 950.4 compilation terminated.
#16 950.5 gmake[5]: *** [Common/Core/CMakeFiles/CommonCore-objects.dir/build.make:356: Common/Core/CMakeFiles/CommonCore-objects.dir/vtkArrayBulkInstantiate_float.cxx.o] Error 1
#16 1057.8 gmake[4]: *** [CMakeFiles/Makefile2:13575: Common/Core/CMakeFiles/CommonCore-objects.dir/all] Error 2
#16 1057.8 gmake[3]: *** [Makefile:136: all] Error 2
#16 1057.8 gmake[2]: *** [CMakeFiles/VTK.dir/build.make:91: VTK-prefix/src/VTK-stamp/VTK-build] Error 2
```

### 根因定位
- 失败位置: `build-Slicer.sh` 中的 `cmake --build` 阶段，编译 VTK 的 `Common/Core/vtkArrayBulkInstantiate_*.cxx` 时
- 失败原因: 编译器进程 `cc1plus` 被 Linux OOM Killer 杀死（`Killed signal`），构建机内存不足，无法承受并行编译 VTK 大型 C++ 模板实例化文件的峰值内存消耗

### 与 PR 变更的关联
此失败与 PR 代码变更无关。PR 仅新增了 3D Slicer 5.12.0 的 Dockerfile 及配套构建脚本和 patch 文件，这些文件本身逻辑正确（cmake 配置阶段已完成并开始编译，说明脚本和依赖均正确安装）。失败发生在 **CI 基础设施层**：构建机器内存不足以在 `--parallel $NUMBER_OF_PHYSICAL_CORES`（全核心并行编译）模式下完成 VTK 的编译。

## 修复方向

### 方向 1（置信度: 中）
在 `build-Slicer.sh` 的 `cmake --build` 命令中限制并行编译数，不使用全部 CPU 核心，改为固定较小的并行数（如 `--parallel 2` 或 `--parallel 4`），以降低峰值内存占用，避免触发 OOM Killer。这是临时绕过基础设施限制的方案。

### 方向 2（置信度: 中）
检查 CI 构建节点的内存配置。3D Slicer + VTK 全量源码编译是内存密集型任务，如果 CI 分配给 Docker 容器的内存低于 8GB，建议提升构建节点的 RAM 配额或使用更高规格的 runner。

## 需要进一步确认的点
- CI 构建节点的实际内存大小和 Docker 容器的内存限制是多少
- 其他同类 HPC 镜像（如其他需要编译 VTK 的大型 C++ 项目）是否也有类似的 OOM 问题
- 是否可以通过 CMake 的 `CMAKE_BUILD_PARALLEL_LEVEL` 环境变量或 ninja 替代 make 来降低内存压力
