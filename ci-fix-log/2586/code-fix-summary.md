# 修复摘要

## 修复的问题
将 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile` 从无法工作的 conda 安装方式改为源码编译方式，并修复了 SWIG 调用错误和 numpy 头文件路径缺失两个编译失败问题。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 移除 miniconda + conda install 方式，改为 yum 安装依赖 + git clone 源码 + make 编译，并正确配置 SWIG 和 numpy 头文件路径。

## 修复逻辑

CI 分析报告指出了三个关联问题：

1. **`faiss-cpu=20180223` 不存在于 conda 仓库**：faiss 的日期式版本号（2017XXXX/2018XXXX）从未发布为 conda 或 pip 包，仅 1.x 语义化版本号才有 conda 包。原 Dockerfile 的 `conda install faiss-cpu=20180223` 必然失败，导致 CI 自动回退到源码编译路线。修复方案：移除 conda 路线，直接使用源码编译。

2. **SWIG 调用错误**（分析报告错误1）：faiss v20180223 的 Makefile 中 SWIG 变量未定义或回退为 `$(PYTHON)`，导致用 `python` 可执行文件调用 swig（如 `python -c++ -Doverride=`），触发 `SyntaxError: invalid syntax`。修复方案：在 makefile.inc 中显式设置 `SWIG = swig` 和 `SWIGFLAGS = -c++ -Doverride=`。

3. **numpy 头文件缺失**（分析报告错误2）：默认 makefile.inc.Linux 使用 `python -c "import numpy..."` 和 `python-config` 来获取 numpy 头文件路径，但在 openEuler 环境中这些命令可能解析到错误路径或不存在。修复方案：在构建时动态解析 numpy 头文件路径（`python3 -c "import numpy; print(numpy.get_include())"`）和 python3-config includes，将硬编码路径写入 makefile.inc。

修复遵循项目规范（`CLAUDE.md`）：使用 yum 安装依赖、`&&` 链式命令、仅移除 gcc make 的清理策略、`2>/dev/null || true` 容错处理。

## 潜在风险
- faiss v20180223 是 2018 年的旧版本，其源码可能依赖较旧的编译工具链或已废弃的 API，在较新的 openEuler 24.03-lts-sp3 上可能存在其他编译兼容性问题。但从 CI 日志来看，make 主流程已通过，仅 SWIG 和 numpy 头文件两个问题导致失败，修复后应可通过。
- `make py` 生成的 Python 绑定（`_swigfaiss.so` + `swigfaiss.py`）是手动复制到 site-packages 的，如果 faiss 的 Makefile 后续版本变更了产物路径或文件名，需要同步更新复制命令。