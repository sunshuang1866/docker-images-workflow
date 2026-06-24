# CI 失败分析报告

## 基本信息
- PR: #2725 — 【自动升级】3dslicer容器镜像升级至5.12.0版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 编译OOM被Kill
- 新模式症状关键词: Killed signal, terminated program cc1plus, gmake, parallel, OOM

## 根因分析

### 直接错误
```
#16 882.4 c++: fatal error: Killed signal terminated program cc1plus
#16 882.4 gmake[5]: *** [Common/Core/CMakeFiles/CommonCore-objects.dir/build.make:328: Common/Core/CMakeFiles/CommonCore-objects.dir/vtkArrayBulkInstantiate_char.cxx.o] Error 1
#16 950.4 c++: fatal error: Killed signal terminated program cc1plus
#16 950.5 gmake[5]: *** [Common/Core/CMakeFiles/CommonCore-objects.dir/build.make:356: Common/Core/CMakeFiles/CommonCore-objects.dir/vtkArrayBulkInstantiate_float.cxx.o] Error 1
#16 1057.8 gmake[4]: *** [CMakeFiles/Makefile2:13575: Common/Core/CMakeFiles/CommonCore-objects.dir/all] Error 2
#16 1057.8 gmake[3]: *** [Makefile:136: all] Error 2
#16 1057.8 gmake[2]: *** [CMakeFiles/VTK.dir/build.make:91: VTK-prefix/src/VTK-stamp/VTK-build] Error 2
#16 1057.8 gmake[1]: *** [CMakeFiles/Makefile2:694: CMakeFiles/VTK.dir/all] Error 2
#16 1057.8 gmake: *** [Makefile:91: all] Error 2
```

### 根因定位
- 失败位置: VTK 编译阶段（Slicer SuperBuild 子项目），`Common/Core/CMakeFiles/CommonCore-objects.dir/` 中的模板实例化文件
- 失败原因: 编译 `vtkArrayBulkInstantiate_char.cxx.o` 和 `vtkArrayBulkInstantiate_float.cxx.o` 时，`cc1plus` 编译器进程被系统 OOM Killer 终止——内存耗尽。

### 与 PR 变更的关联
PR 引入了全新的 Dockerfile 和构建脚本（`build-CTKAppLauncher.sh`、`build-tbb.sh`、`build-Slicer.sh`）。三个构建脚本均使用 `NUMBER_OF_PHYSICAL_CORES=$(grep -c ^processor /proc/cpuinfo)` 获取全部 CPU 核心数，并以 `--parallel $NUMBER_OF_PHYSICAL_CORES` 传递给 cmake 进行全核并行编译。VTK 中的模板量级文件（`vtkArrayBulkInstantiate_*.cxx`）单文件编译内存消耗极大，全核并行导致 CI runner 内存耗尽，触发 OOM Killer。该问题与 PR 代码变更直接相关——构建脚本中的并行度策略是触发点。

## 修复方向

### 方向 1（置信度: 高）
在 `build-Slicer.sh`（及可能的其他构建脚本）中，对并行编译核数设置上限（如 `-j$(($NUMBER_OF_PHYSICAL_CORES / 2))` 或固定 `-j4`），避免 VTK 等大型 C++ 子项目的模板实例化编译在 CI 有限内存的环境中触发 OOM。同时可考虑为 cmake 添加 `-DCMAKE_CXX_FLAGS="-g0"` 等减小编译内存占用的标志。

### 方向 2（置信度: 中）
若 Slicer 的 cmake 构建系统支持，可在 SuperBuild 的 VTK 配置阶段传入 `-DVTK_SMP_IMPLEMENTATION_TYPE=Sequential` 或减少 `VTK_GROUP_ENABLE_*` 模块以减少编译单元数量，降低总体编译内存需求。

## 需要进一步确认的点
- CI runner 的实际内存配置（以确定合理的并行度上限）
- VTK 9.6（Slicer 5.12.0 依赖的版本）的 `vtkArrayBulkInstantiate_*.cxx` 文件大小和编译内存需求
- 是否可以在 Docker build 时通过 `--memory` 限制或 BuildKit 资源参数从外部控制编译内存

## 修复验证要求
code-fixer 修改构建脚本后，需在同等内存配置的 CI 环境中重新触发构建，确认 VTK 编译阶段不再出现 `Killed signal` 错误且构建能成功完成。若降并行度后编译超时，需进一步评估是否需要在 cmake 配置阶段关闭不必要的 VTK 模块以缩减编译规模。
