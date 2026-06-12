# 修复摘要

## 修复的问题
修复 OpenFOAM 2512 Dockerfile 中 ThirdParty 下载 URL 的扩展名不匹配（`.tgz` → `.tar.gz`），解决 SourceForge 返回 404 导致的构建失败。

## 修改的文件
- `HPC/openfoam/2512/24.03-lts-sp3/Dockerfile`: 将 `ThirdParty-v${VERSION}.tgz` 改为 `ThirdParty-v${VERSION}.tar.gz`（共 3 处：wget、tar、rm）

## 修复逻辑
SourceForge 上 v2512 目录中，`ThirdParty-v2512` 的实际文件名扩展名为 `.tar.gz`（区别于旧版本 v2506/v2412 使用的 `.tgz`）。Dockerfile 中硬编码了 `.tgz` 扩展名，导致 wget 请求 `ThirdParty-v2512.tgz` 时返回 404。将 ThirdParty 相关的 3 处引用从 `.tgz` 改为 `.tar.gz` 即可匹配上游实际文件名。`tar -xvf` 会自动检测压缩格式，无需额外处理。

## 潜在风险
无。仅修改了 ThirdParty 文件名的扩展名部分，不影响 OpenFOAM 主体源码下载（`OpenFOAM-v2512.tgz` 保持 `.tgz` 不变，与上游一致）。