# CI 失败分析报告

## 基本信息
- PR: #2593 — 【自动升级】vllm-cpu容器镜像升级至0.23.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 并行编译内存溢出
- 新模式症状关键词: `Killed signal terminated program cc1plus`, `compilation terminated`, `ninja: build stopped`, OOM, `-j=8`

## 根因分析

### 直接错误
```
#13 1037.2 [456/479] Building CXX object CMakeFiles/_C.dir/csrc/cpu/cpu_attn.cpp.o
#13 1037.2 FAILED: [code=1] CMakeFiles/_C.dir/csrc/cpu/cpu_attn.cpp.o
#13 1037.2 ccache /usr/bin/c++ -DCPU_CAPABILITY_AMXBF16 ...
#13 1037.2 c++: fatal error: Killed signal terminated program cc1plus
#13 1037.2 compilation terminated.
...
#13 1125.1 ninja: build stopped: subcommand failed.
#13 1125.1 subprocess.CalledProcessError: Command '['cmake', '--build', '.', '-j=8', '--target=spinloop', '--target=_C', '--target=_C_AVX512', '--target=_C_AVX2']' returned non-zero exit status 1.
```

### 根因定位
- 失败位置: `Dockerfile:41` — `RUN VLLM_TARGET_DEVICE=cpu python3 setup.py bdist_wheel`
- 失败原因: `setup.py` 内部调用 cmake 构建时使用 `-j=8` 并行编译，`cpu_attn.cpp` (含 AMXBF16 指令集的重量级模板代码) 编译时消耗内存过大，`cc1plus` 被 Linux OOM Killer 杀死

### 与 PR 变更的关联
- PR 新增了整个 `AI/vllm-cpu/0.23.0/24.03-lts-sp3/Dockerfile`（52 行），触发 vllm 0.23.0 源码的完整 C++ 编译
- 该失败由 **PR 新增的构建流程** 直接触发，但并非代码逻辑错误——是 CI 构建节点的内存资源不足以支撑 8 路并行编译 vllm 0.23.0 的全部 C++ 目标（含 oneDNN 479 个编译单元 + 多个 CMAKE target）
- 对比：历史成功的 vllm-cpu 版本（0.16.0、0.18.0、0.20.1）可能存在相同的 OOM 风险，但此前版本源码规模较小或编译目标较少，未触及内存上限

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `build` stage 中，于 `python3 setup.py bdist_wheel` 命令前设置环境变量降低并行度，例如通过 `MAX_JOBS` 或 `CMAKE_BUILD_PARALLEL_LEVEL` 限制 cmake 编译并行数为 `4` 或 `2`：
```
ENV MAX_JOBS=4
RUN VLLM_TARGET_DEVICE=cpu python3 setup.py bdist_wheel
```
或者通过 ninja 的 `-j` 参数覆盖，在 `setup.py` 调用前设置 `CMAKE_BUILD_PARALLEL_LEVEL=4`。

### 方向 2（置信度: 中）
如果 CMake 的 `-j=8` 不受环境变量控制（由 setup.py 硬编码），可在 `pip install -r requirements/build/cpu.txt` 之后、`setup.py bdist_wheel` 之前，用 `sed` 修改 `setup.py` 中的 `-j=8` 参数为较小值（如 `-j=4`）。

## 需要进一步确认的点
- 确认 vllm 0.23.0 的 `setup.py` 中 `-j=8` 的具体产生方式（是 `nproc` 自动检测还是硬编码），以判断方向 1 的环境变量方式是否生效
- 与历史成功的 vllm-cpu 版本（0.20.1、0.18.0）对比 CI 节点的内存配置是否一致，排除 CI 基础设施缩容的可能性
