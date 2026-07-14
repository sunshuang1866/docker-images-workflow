# 修复摘要

## 修复的问题
将 Wireshark 4.6.5 源码下载 URL 从主路径改为归档路径，修复 HTTP 404 错误导致的 Docker 构建失败。

## 修改的文件
- `Others/wireshark/4.6.5/24.03-lts-sp4/Dockerfile`: 第13行，wget 下载 URL 添加 `all-versions/` 子路径

## 修复逻辑
Wireshark 官方将非最新版本（包括 4.6.5）的源码包从主下载目录 `download/src/` 迁移到了归档目录 `download/src/all-versions/`。Dockerfile 原 URL `https://www.wireshark.org/download/src/wireshark-${VERSION}.tar.xz` 返回 404，修改为 `https://www.wireshark.org/download/src/all-versions/wireshark-${VERSION}.tar.xz` 后文件可正常访问。已从上游获取该归档 URL 验证，确认文件存在。

## 潜在风险
无。仅修改下载路径，不改变构建逻辑。同版本的 SP3 Dockerfile 使用相同的主路径 URL，但不在本次 PR 变更范围内，未做修改。