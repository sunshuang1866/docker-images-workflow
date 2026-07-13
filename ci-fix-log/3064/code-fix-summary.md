# 修复摘要

## 修复的问题
phono3py 4.1.0 上游 `pyproject.toml` 使用了已废弃的 `cmake.verbose` 配置项，与 scikit-build-core >= 0.10 不兼容，导致 `pip3 install .` 在 "Getting requirements to build wheel" 阶段报错退出（exit code 7）。

## 修改的文件
- `HPC/phono3py/4.1.0/24.03-lts-sp4/Dockerfile`: 在第 13 行新增 `sed -i 's/cmake\.verbose/build.verbose/g' pyproject.toml` 命令，在 `pip3 install .` 之前将废弃配置项替换为兼容名称。

## 修复逻辑
1. 从 phono3py v4.1.0 上游仓库获取了 `pyproject.toml`（tag `v4.1.0`），确认其中 `[tool.scikit-build]` 段下存在 `cmake.verbose = true` 配置。
2. 用 Python 验证了 `sed` 正则模式 `s/cmake\.verbose/build.verbose/g` 能正确匹配并替换，不会误伤其他字段。
3. 在 `git clone` 之后、`pip3 install .` 之前插入 `sed` 命令，对刚克隆的源码做就地替换，使构建配置与 scikit-build-core >= 0.10 兼容。

## 潜在风险
无。该修复仅将 `pyproject.toml` 中的一个布尔型配置项名称从 `cmake.verbose` 改为 `build.verbose`，两者语义完全相同，不影响构建行为。替换操作只针对已克隆到容器内的临时源码，不修改上游仓库。