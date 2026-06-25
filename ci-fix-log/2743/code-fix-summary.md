# 修复摘要

## 修复的问题
SeisSol 202103.Sumatra 的 CMakeLists.txt 无 `install()` 目标，`cmake --install build` 不安装任何文件，导致 stage-1 的 `COPY --from=builder /usr/local/bin/SeisSol*` 找不到文件。

## 修改的文件
- `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile`: 将第 79 行 `cmake --install build` 替换为 `cp build/SeisSol_Release_*_4_elastic build/SeisSol_proxy_Release_*_4_elastic /usr/local/bin/`，直接拷贝构建产物到 `/usr/local/bin/`。

## 修复逻辑
SeisSol 202103_Sumatra 的顶层 CMakeLists.txt 定义了 `SeisSol-bin` 和 `SeisSol-proxy` 两个可执行目标，但未定义 `install(TARGETS ...)` 规则，导致 `cmake --install build` 无实际操作（构建日志仅输出 `-- Install configuration: "Release"`，无 `-- Installing:` 行）。二进制文件实际位于 `build/SeisSol_Release_dnoarch_4_elastic` 和 `build/SeisSol_proxy_Release_dnoarch_4_elastic`。

已从上游 `https://raw.githubusercontent.com/SeisSol/SeisSol/202103_Sumatra/CMakeLists.txt` 和 `cmake/process_users_input.cmake` 获取源文件验证：
- `HOST_ARCH=noarch` + `PRECISION=double` → `HOST_ARCH_STR=dnoarch`
- `EXE_NAME_PREFIX=Release_dnoarch_4_elastic`
- 目标输出名：`SeisSol_Release_dnoarch_4_elastic`、`SeisSol_proxy_Release_dnoarch_4_elastic`
- `add_executable` 在顶层 CMakeLists.txt 定义，产物在 `${CMAKE_CURRENT_BINARY_DIR}` 即 `build/` 目录

用 Python `fnmatch` 验证 glob 模式 `SeisSol_Release_*_4_elastic` 和 `SeisSol_proxy_Release_*_4_elastic` 均能匹配上述实际文件名，确认匹配成功。

替换后，`cp` 将二进制拷贝至 `/usr/local/bin/`，后续 `ln -sf` 能正常创建 `SeisSol` 符号链接，stage-1 的 `COPY --from=builder /usr/local/bin/SeisSol*` 可找到文件。

## 潜在风险
无。`cmake --install build` 原本就是空操作，替换为直接的 `cp` 命令不改变其他行为。若未来 SeisSol 版本升级后 CMakeLists.txt 新增 `install()` 规则，该 `cp` 命令仍可正常执行（二进制文件会同时存在，cp 覆盖不影响结果）。