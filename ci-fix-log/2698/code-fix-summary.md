# 修复摘要

## 修复的问题
GitHub `archive/refs/tags/` 自动生成的源码 tarball 不包含 git submodule 内容，导致 `extra/libkmip` 目录为空，cmake 配置阶段报 `does not contain a CMakeLists.txt file` 错误。

## 修改的文件
- `Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile`: 将源码获取方式从 `wget` 下载 GitHub tarball 改为 `git clone --recurse-submodules`，确保 submodule（包括 `extra/libkmip`）被完整拉取；同时在 `dnf install` 中添加 `git` 包。

## 修复逻辑
分析报告指出 percona-server 仓库中 `extra/libkmip` 是一个 git submodule（`.gitmodules` 中确认为 `url = https://github.com/Percona-Lab/libkmip.git`），GitHub 的 `archive/refs/tags/` 接口生成的 tarball 不包含 submodule 内容，导致该目录存在但缺少 `CMakeLists.txt`，cmake 的 `ADD_SUBDIRECTORY` 调用失败。

修复采用方向1（置信度: 高）：将源码获取方式从下载 tarball 改为 `git clone --recurse-submodules --branch "Percona-Server-${VERSION}-${RELEASE}" https://github.com/percona/percona-server.git /percona`。`git clone` 加 `--recurse-submodules` 会递归克隆所有 submodule，确保 `extra/libkmip/CMakeLists.txt` 存在，cmake 配置不再报错。

已从上游 `Percona-Server-8.4.8-8` tag 获取 `.gitmodules` 文件验证，`extra/libkmip` 确认为 submodule，修复方案匹配正确。

## 潜在风险
- `git clone` 比 `wget` 下载 tarball 更耗时（需要完整克隆仓库历史），但这是唯一能正确拉取 submodule 的方式。
- 引入 `git` 包到构建依赖中，后续 `dnf -y remove` 未移除 `git`（与 `wget` 的处理方式一致），对最终镜像大小有轻微影响。如需精简可后续在 cleanup 阶段添加 `git` 到移除列表。