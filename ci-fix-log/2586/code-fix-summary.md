# 修复摘要

## 修复的问题
conda channel 中不存在 `faiss-cpu=20180223` 包，导致 Docker 镜像构建失败（PackagesNotFoundInChannelsError）。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 移除 conda 安装 `faiss-cpu=${VERSION}`，改为通过 dnf 安装编译依赖并从 GitHub 源码编译安装 FAISS。

## 修复逻辑
CI 失败分析报告指出根因是 `faiss-cpu=20180223` 在 conda 的 pytorch/conda-forge/defaults 三个 channel 中均不存在。`20180223` 是 FAISS 上游仓库的日期式 Git tag（如 2018-02-23），而 conda channel 中的 `faiss-cpu` 包使用语义化版本（如 1.14.1），两者不匹配。

由于该早期版本在 conda 和 PyPI 中均无对应的包，按照分析报告中"方向 2：从源码编译安装"的建议，以及参考同仓库中 AI 类 Dockerfile（如 diskann、tvm、caffe、pytorch 等）普遍采用的 `dnf install 编译依赖 + git clone/curl tar.gz + make + python setup.py install` 的源码构建模式，将安装方式改为：
1. dnf 安装编译依赖（gcc-c++、make、openblas-devel）
2. 从 GitHub 下载对应 tag 的源码包
3. make 编译 C++ 库
4. python setup.py install 安装 Python 绑定
5. 清理临时文件

## 潜在风险
FAISS v20180223（2018 年版本）可能不兼容 Python 3.12，导致后续编译或运行时错误。但当前 CI 失败是 conda 包不存在的依赖问题，不是语法兼容性问题。若编译阶段出现兼容性问题，需进一步排查 Python/编译器版本的兼容性。