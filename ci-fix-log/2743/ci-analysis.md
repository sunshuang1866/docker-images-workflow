# CI 失败分析报告

## 基本信息
- PR: #2743 — 【自动升级】seissol容器镜像升级至202103.Sumatra版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式06（症状相似，根因不同）+ 模式20（副作用）
- 新模式标题: cmake install 无安装规则
- 新模式症状关键词: failed to calculate checksum, not found, SeisSol, cmake --install, COPY --from=builder

## 根因分析

### 直接错误

```
#15 [stage-1 3/8] COPY --from=builder /usr/local/bin/SeisSol* /usr/local/bin/
#15 ERROR: failed to calculate checksum of ref 3z3utj5dde0nqcbrj72gahkpr::z7rqbv3f2iw30ji9201thbrbj: "/usr/local/bin/SeisSol": not found
ERROR: failed to solve: failed to compute cache key: failed to calculate checksum of ref 3z3utj5dde0nqcbrj72gahkpr::z7rqbv3f2iw30ji9201thbrbj: "/usr/local/bin/SeisSol": not found

 1 warning found (use --debug to expand):
 - UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 98)
Dockerfile:90
--------------------
  90 | >>> COPY --from=builder /usr/local/bin/SeisSol* /usr/local/bin/
```

### 根因定位

- 失败位置: Dockerfile 第 90 行，stage-1（运行阶段）的 `COPY --from=builder /usr/local/bin/SeisSol*`
- 失败原因: builder 阶段中 `cmake --install build` 未将 SeisSol 可执行文件实际安装到 `/usr/local/bin/` 目录。从日志中可见 cmake install 输出仅有一行 `-- Install configuration: "Release"`，无任何 `-- Installing:` 行（正常 install 会逐文件打印安装路径），说明 SeisSol 202103.Sumatra 的 CMakeLists.txt **未定义 `install()` 目标**，导致构建产物留在 build 目录而未被拷贝到安装前缀。build 阶段因 `&&` 链中所有命令（`cmake --install build`、`ln -sf`、`rm -rf`）均返回 0 而标记成功，但实际在 `/usr/local/bin/` 下无有效文件。stage-1 的 `COPY --from=builder /usr/local/bin/SeisSol*` 找不到任何匹配文件，BuildKit 报错。

### 与 PR 变更的关联

PR 新增了 SeisSol 202103.Sumatra 版本的 Dockerfile，这是一个全新的文件。问题出在该 Dockerfile 的 3 阶段构建流程中：builder 阶段编译 SeisSol 后依赖 `cmake --install build` 将二进制安装至 `/usr/local/bin/`，但 SeisSol 的 CMake 项目未提供 install 规则，导致后续 COPY 步骤找不到目标文件。**该失败由这次 PR 引入的 Dockerfile 直接触发**，与之前已有的 SeisSol 1.3.2 版本 Dockerfile（如构建流程不同）无关。

额外存在一个 BurildKit 警告（模式20）：第 98 行 `ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 自引用了未定义的 `$LD_LIBRARY_PATH`，应改为 `${LD_LIBRARY_PATH:-}`。

## 修复方向

### 方向 1（置信度: 中）
将 `cmake --install build` 替换为手动拷贝构建产物。SeisSol 的 CMake 构建在 `build/` 目录下生成了实际的可执行文件（`SeisSol_Release_dnoarch_4_elastic` 和 `SeisSol_proxy_Release_dnoarch_4_elastic`），可以直接用 `cp` 或 `install` 命令将它们从 build 目录拷贝到 `/usr/local/bin/`，再创建对应的符号链接 `SeisSol`。这样做不依赖 SeisSol CMake 项目的 install 目标是否存在。

### 方向 2（置信度: 低）
为 SeisSol 202103.Sumatra 的 CMakeLists.txt 添加 `install(TARGETS ...)` 规则（通过 patch 方式在 Dockerfile 中 `sed` 或 `git apply`），使 `cmake --install` 能正确安装。但这需要了解 SeisSol 的 CMake 项目结构，且不同版本的 CMakeLists.txt 可能结构差异大，维护成本高。

## 需要进一步确认的点

1. **SeisSol 202103.Sumatra 源码中 `src/` 目录的 CMakeLists.txt 是否确实没有 `install(TARGETS SeisSol-bin ...)` 规则**。可从上游仓库 `https://github.com/SeisSol/SeisSol.git` 的 `v202103.Sumatra` tag 拉取源码确认。
2. **已有的 SeisSol 1.3.2 Dockerfile 是如何处理二进制安装的**。如果 1.3.2 版本也使用 `cmake --install` 并能成功，说明 1.3.2 版本的 CMake 项目有 install 规则，需对比两者的构建方式差异。
3. **构建产物在 build 目录下的具体路径和确切文件名**，以便在修复方向 1 中使用正确的 `cp` 命令。
4. **修复 LD_LIBRARY_PATH 的 UndefinedVar 警告**（第 98 行改为 `${LD_LIBRARY_PATH:-}`），这是每次构建都会产生的警告，与模式20一致。

## 修复验证要求

若采用修复方向 1（手动拷贝构建产物），code-fixer **必须**：
1. 从上游仓库 `https://github.com/SeisSol/SeisSol.git` 拉取 `v202103.Sumatra` tag 的源码
2. 在目标平台（openEuler 24.03-lts-sp3）上本地运行 cmake 构建，记录构建产物在 build 目录下的确切路径和文件名
3. 确认 `cp`/`install` 命令能正确拷贝所有需要的二进制文件
4. 修改 Dockerfile 后重新完整构建镜像验证
