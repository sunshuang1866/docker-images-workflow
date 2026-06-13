# 修复摘要

## 修复的问题
Dockerfile 中缺少 faiss v20180223 旧版构建系统所需的 `cp example_makefiles/makefile.inc.Linux makefile.inc` 步骤，且 conda 未提供该旧版本的预编译包，需从源码构建。

## 修改的文件
- `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`: 将 conda 安装 faiss-cpu 替换为源码构建方式，添加构建依赖、makefile.inc 复制步骤及编译安装流程。

## 修复逻辑
CI 分析报告指出根因为旧版 faiss 构建系统要求在 `make` 前从 `./example_makefiles/` 复制平台对应的 `makefile.inc` 到项目根目录。修改后的 RUN 指令：
1. 通过 conda 安装 python=3.12 和 numpy（保留 conda 提供 Python 运行时）
2. 通过 dnf 安装 gcc-c++、make、openblas-devel 等编译依赖
3. 下载 faiss 源码包并解压
4. **在 `make` 前执行 `cp example_makefiles/makefile.inc.Linux makefile.inc`**（核心修复）
5. 编译 faiss 库并安装 Python 绑定
6. 清理临时文件

## 潜在风险
- `example_makefiles/makefile.inc.Linux` 模板可能需要针对 openEuler 环境的 BLAS 库路径做调整（如 openblas 路径），如果编译成功但运行时链接失败，需进一步修改 makefile.inc 中的 BLAS 路径配置。