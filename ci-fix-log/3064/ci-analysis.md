# CI 失败分析报告

## 基本信息
- PR: #3064 — chore(phono3py): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: scikit-build-core 配置项重命名
- 新模式症状关键词: cmake.verbose, build.verbose, scikit-build-core >= 0.10, Getting requirements to build wheel

## 根因分析

### 直接错误
```
#8 15.43   Installing build dependencies: finished with status 'done'
#8 15.44   Getting requirements to build wheel: started
#8 15.55   Getting requirements to build wheel: finished with status 'error'
#8 15.56   error: subprocess-exited-with-error
#8 15.56   × Getting requirements to build wheel did not run successfully.
#8 15.56   │ exit code: 7
#8 15.56   ╰─> [1 lines of output]
#8 15.56       ERROR: Use build.verbose instead of cmake.verbose for scikit-build-core >= 0.10
#8 15.56       [end of output]
```

### 根因定位
- 失败位置: `HPC/phono3py/4.1.0/24.03-lts-sp4/Dockerfile:10-14`（第 3 个 RUN 指令中的 `pip3 install --no-cache-dir .` 步骤）
- 失败原因: phono3py 4.1.0 源码中的 `pyproject.toml` 使用了已废弃的 `cmake.verbose` 配置项，而 pip install 自动安装的 scikit-build-core >= 0.10 已将该配置项重命名为 `build.verbose`，导致构建轮子前的 "getting requirements" 阶段直接报错退出（exit code 7）。

### 与 PR 变更的关联
PR #3064 新增了 `HPC/phono3py/4.1.0/24.03-lts-sp4/Dockerfile`，其中第 10 行的 `pip3 install .` 从 GitHub 克隆 phono3py 4.1.0 源码并在当前环境编译安装。phono3py v4.1.0 上游源码中 `pyproject.toml` 使用了旧版 `[tool.scikit-build]` 下的 `cmake.verbose` 键，与 `pip install` 过程中拉取的最新版 scikit-build-core（>= 0.10）不兼容。此问题**由 PR 新增的 Dockerfile 直接触发**，因为 phono3py 的构建流程对上游 scikit-build-core 版本敏感。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `pip3 install .` 之前，用 `sed` 将 phono3py 源码中 `pyproject.toml`（或 `CMakeLists.txt` 对应的 scikit-build cmake 模块）里的 `cmake.verbose` 替换为 `build.verbose`，使构建配置与当前环境下自动安装的 scikit-build-core >= 0.10 兼容。

### 方向 2（置信度: 中）
在 `pip3 install .` 之前，通过 `pip3 install "scikit-build-core<0.10"` 将 scikit-build-core 版本锁定在 0.10 以下，然后让 phono3py 构建自动使用已安装的旧版 scikit-build-core。此方式可行但有风险：旧版 scikit-build-core 可能与其他依赖产生兼容性问题，且长期来看属于规避性修复。

## 需要进一步确认的点
- phono3py 4.1.0 源码中具体使用 `cmake.verbose` 的文件路径和行号（`pyproject.toml` 或 CMake 相关文件），以便精确定位 sed 替换目标。
- 通过本地 docker build 验证修复后的 Dockerfile 能否完整通过构建。

## 修复验证要求
code-fixer 在提交前，必须从 phono3py v4.1.0 上游仓库（`https://github.com/phonopy/phono3py.git`，tag `v4.1.0`）获取 `pyproject.toml` 及 CMake 相关配置文件，确认 `cmake.verbose` 的实际使用位置，验证 sed 替换/锁定版本方案在目标文件上能正确生效后再提交。
