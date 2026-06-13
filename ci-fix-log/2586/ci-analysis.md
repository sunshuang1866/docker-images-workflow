# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Numpy头文件缺失
- 新模式症状关键词: numpy/arrayobject.h, No such file or directory, make py, swigfaiss_wrap.cxx, conda numpy headers

## 根因分析

### 直接错误
```
#8 724.0 g++ -I. -fPIC -m64 -Wall -g -O3 -mavx -msse4 -mpopcnt -fopenmp -Wno-sign-compare -std=c++11 -fopenmp -g -fPIC  -fopenmp -I/opt/conda/include/python3.12 -I/opt/conda/lib/python3.12/site-packages/numpy/core/include -shared \
#8 724.0 -o python/_swigfaiss.so python/swigfaiss_wrap.cxx libfaiss.a /usr/lib64/libopenblas.so.0
#8 724.0 python/swigfaiss_wrap.cxx:3228:10: fatal error: numpy/arrayobject.h: No such file or directory
#8 724.0  3228 | #include <numpy/arrayobject.h>
#8 724.0       |          ^~~~~~~~~~~~~~~~~~~~~
#8 724.0 compilation terminated.
#8 724.1 make: *** [Makefile:84: python/_swigfaiss.so] Error 1
#8 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `python/swigfaiss_wrap.cxx:3228`（faiss 源码中 SWIG 生成的 Python 绑定文件）
- 失败原因: `make py` 编译 SWIG 绑定文件时找不到 numpy C 头文件 `numpy/arrayobject.h`。尽管 `conda install numpy` 已执行且 include 路径 `-I/opt/conda/lib/python3.12/site-packages/numpy/core/include` 已传入，但 numpy 包可能未在该路径下安装 C 开发头文件（主 channel 的 numpy 包可能不包含 C API 头文件，或路径结构与预期不同）。

### 与 PR 变更的关联
**存在关键歧义**：PR diff 中的 Dockerfile（21 行）仅执行 `conda install faiss-cpu=${VERSION}` 从 conda-forge 预编译包安装，不涉及任何源码构建。但 CI 日志中的 Dockerfile（29+ 行）执行了完整的 faiss 源码构建流程（dnf 安装编译工具链 → 下载源码 → make 编译 C++ 库 → make py 编译 Python 绑定）。二者内容不一致。CI 日志中报错的那个 Dockerfile 采用了"源码构建"方案，该方案需要 numpy 开发头文件来完成 SWIG 绑定编译，而正是此步骤失败。

可能的原因：
1. Jenkins 管道在 checkout 后自动扩充 / 修改了 Dockerfile
2. PR 提交后存在 force-push，diff 与 CI 实际运行的版本不一致
3. CI 触发了不同的构建上下文

无论哪种情况，**失败由 CI 日志中的 Dockerfile（源码构建版）引起**，而非 PR diff 中的版本。如果 PR diff 版本（纯 conda 安装）被实际构建，则不会触发此错误。

## 修复方向

### 方向 1（置信度: 中）
如果采用 CI 日志中的"源码构建"方案：需要确保 numpy 头文件在编译 `make py` 前可用。可能的做法：
- 将 `conda install numpy` 改为 `conda install -c conda-forge numpy` 确保安装包含 C 头文件的版本
- 或者在 `make py` 前先验证 `numpy/arrayobject.h` 在 include 路径下存在
- 或者使用 `numpy.get_include()` 动态获取 numpy include 路径，而非硬编码

### 方向 2（置信度: 中）
如果采用 PR diff 中的"conda 预编译包"方案：Dockerfile 只需 `conda install -y -c pytorch -c conda-forge python=3.12 faiss-cpu=${VERSION}`，不涉及源码编译，自然不依赖 numpy 头文件。但需要确认 conda-forge 的 `faiss-cpu=20180223` 包是否存在——20180223 是非常旧的 faiss 版本号（faiss 2018年2月23日发布），conda-forge 可能不托管此版本的预编译包。

## 需要进一步确认的点
1. **PR diff 与 CI 实际运行的 Dockerfile 为何不一致**（最关键的待确认项）。需要查看当前 PR 分支上的实际 Dockerfile 内容，确认到底采用了"conda 预编译"还是"源码构建"方案。
2. conda-forge 频道是否托管 `faiss-cpu=20180223` 预编译包（`conda install -c conda-forge faiss-cpu=20180223` 是否能找到包）。
3. 当前运行环境中 `conda install numpy` 后 `numpy/arrayobject.h` 的实际路径，以及 numpy 版本号（`numpy.get_include()` 返回的路径）。
4. 如果采用源码构建方案，`faiss 20180223`（即 faiss v1.0）的 SWIG 绑定是否与 Python 3.12 + 现代 numpy 兼容（古老版本可能使用已弃用的 numpy C API）。
