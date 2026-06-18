# 修复摘要

## 修复的问题
nDPI 5.0 Dockerfile 构建流程缺少 `./configure` 步骤，导致 make 因找不到 Makefile 而失败。

## 修改的文件
- `Others/ndpi/5.0/24.03-lts-sp3/Dockerfile`: 在 `./autogen.sh` 和 `make` 之间插入 `./configure &&`，补全 autotools 标准构建流程。

## 修复逻辑
nDPI 5.0 的 `autogen.sh` 相比 4.14 版本移除了内部调用的 `./configure`（源码中注释说明："Don't call `configure` here!!!! It breaks out-of-tree builds"），仅生成 configure 脚本而不执行。因此需要在 Dockerfile 中显式调用 `./configure` 来生成 Makefile，然后再执行 `make`。已从上游 5.0 tag 获取 `autogen.sh` 验证，确认该版本不自动执行 configure。

## 潜在风险
无。这是 autotools 项目的标准三阶段构建流程（autogen → configure → make），不传递额外参数时 `./configure` 会自动检测已安装的依赖（libpcap-devel 等）。其他 nDPI 版本（4.12/4.14）的 Dockerfile 不受影响，因为其 `autogen.sh` 内置了 configure 调用。