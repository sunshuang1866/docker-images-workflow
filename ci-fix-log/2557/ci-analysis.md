# CI 失败分析报告

## 基本信息
- PR: #2557 — fix: Add 3FS Image (fix #2512)
- 失败类型: `dependency-error`
- 置信度: 高
- 知识库匹配: 模式10 + 新模式
- 新模式标题: RPM包名不存在
- 新模式症状关键词: `Unable to find a match`, `No match for argument`, `boost-foundation`, `yum`, `开源组件RPM包名映射错误`

## 根因分析

### 直接错误

**致命错误（步骤 #12，Dockerfile:41）：**
```
#12 16.84 Error: Unable to find a match: boost-foundation
#12 ERROR: process "/bin/sh -c yum -y install fuse3-libs openssl-libs lz4 xz-libs \
  double-conversion libdwarf libunwind libaio gflags glog gperftools boost-foundation \
  boost-filesystem boost-system boost-program-options libuv && yum clean all" \
  did not complete successfully: exit code: 1
```

**次要错误（步骤 #10，CMake 配置阶段）：**
```
#10 77.34 CMake Error at third_party/folly/build/fbcode_builder/CMake/FindLibEvent.cmake:68 (message):
#10 77.34 -- Configuring incomplete, errors occurred!
```

### 根因定位

- **失败位置**: 新增的 3FS Dockerfile（`Storage/3fs/<version>/<oe-version>/Dockerfile`）第 41 行
- **失败原因**: Dockerfile 的 `yum install` 命令中使用了 **openEuler RPM 仓库中不存在的包名**：
  - `boost-foundation` — openEuler 中无此 RPM 包名（可能是从其他发行版如 Ubuntu 的 `libboost-foundation-dev` 错误映射而来）
  - `boost-filesystem`、`boost-system`、`boost-program-options` — 这些在 openEuler 中**可能**不是独立的 RPM 包，而均包含在 `boost-devel` 统一开发包中
  - 同时，CMake 配置阶段报 `Could NOT find libevent`（匹配**模式10**），说明还缺 `libevent-devel` 包

### 与 PR 变更的关联

PR #2557 新增 3FS 容器镜像。虽然提供的 diff 仅显示了 `.agents/` 目录下文件的删除（`CLAUDE.md`、`agents/*.md`、`run_workflow.py`），这些删除与构建失败无关。真正的根因在**PR 新增的 3FS Dockerfile**中：

1. Dockerfile 第 41 行的 `yum install` 命令中使用了错误的 RPM 包名 `boost-foundation`，该包名在任何 openEuler 版本仓库中均不存在
2. 缺少 `libevent-devel` 导致 CMake 配置阶段 `FindLibEvent.cmake` 失败（此错误在当前 yum 步骤失败后被掩盖，但即使修复包名后仍需处理）
3. 根据模式18的历史记录，3FS 镜像此前还存在 `git clone --depth 1` 与 commit hash checkout 不兼容的问题（PR #2512、#2526），需一并关注

## 修复方向

### 方向 1：纠正 RPM 包名（置信度: 高）
将 Dockerfile 第 41 行的 yum install 命令中无效包名替换为 openEuler 实际可用的包名：
- `boost-foundation` → 移除（openEuler 无此包，其内容由 `boost-devel` 提供）
- `boost-filesystem`、`boost-system`、`boost-program-options` → 合并为 `boost-devel`（openEuler 中 boost 开发库统一由 `boost-devel` 提供，参考仓库内其他 Dockerfile 如 `Storage/lizardfs`、`Others/hyperscan`、`HPC/qmcpack` 等均使用 `boost-devel`）
- 新增 `libevent-devel`（解决模式10中 CMake 找不到 libevent 的问题）

### 方向 2：验证其他包名是否存在（置信度: 中）
确认 `fuse3-libs`、`double-conversion`、`libdwarf`、`gflags`、`glog`、`gperftools`、`libuv`、`lz4`、`xz-libs`、`libaio`、`libunwind` 等包名在目标 openEuler 版本（24.03-lts-sp3）的 RPM 仓库中均实际存在。部分包名在不同发行版间有差异:
- `libuv` → 确认是 `libuv` 还是 `libuv-devel`
- `xz-libs` → 可能需要 `xz-devel`

### 方向 3：确认 3FS 编译需要的是运行时库还是开发库（置信度: 中）
当前 yum install 安装的全部是运行时库（无 `-devel` 后缀）。但步骤 #10 的 CMake 配置（`third_party/folly` 构建）明确需要开发库头文件。应在 Dockerfile 的前期构建阶段（build stage）安装对应的 `-devel` 包，只在最终运行阶段保留运行时库。

## 需要进一步确认的点

1. **Dockerfile 完整内容不可见**：提供的 PR diff 仅展示了 `.agents/` 文件的删除，未包含新增的 3FS Dockerfile 完整内容。需要查看完整的 `Storage/3fs/<commit-hash>/<oe-version>/Dockerfile` 以确认完整的包列表和构建逻辑。
2. **3FS 实际依赖清单**：需对照 3FS 源码（仓库 `github.com/deepseek-ai/3FS` 或类似上游）的 `README` / `CMakeLists.txt` 确认完整的编译依赖列表，尤其确认 folly 和其子依赖（libevent、double-conversion、gflags、glog、gperftools 等）的正确包名映射。
3. **openEuler 24.03-lts-sp3 包名确认**：在目标基础镜像内执行 `yum search boost`、`yum search libevent` 确认可用包的确切名称，避免再次使用不存在的包名。
4. **模式18遗留问题**：根据历史模式，PR #2512 曾因 `git clone --depth 1` + commit hash checkout 失败。当前 PR 声称 fix #2512，需确认 Dockerfile 中 git 克隆逻辑是否已正确修复——去掉 `--depth 1` 或先 `git fetch` 再 checkout。
