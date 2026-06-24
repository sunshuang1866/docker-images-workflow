# 修复摘要

## 修复的问题
openEuler 24.03-lts-sp3 基础镜像的 yum 源安装的 CMake (3.27.9) 不满足 Slicer 5.12.0 对 CMake >= 3.28.0 的要求，导致 cmake 配置阶段失败。

## 修改的文件
- `HPC/3dslicer/5.12.0/24.03-lts-sp3/Dockerfile`: 从 yum 安装列表中移除 `cmake`，添加 `wget`，新增从 CMake 官方 GitHub Releases 下载并安装 CMake 3.28.6 预编译二进制包的步骤。

## 修复逻辑
根因是 CI 分析报告中的 **CMake版本过低**：Slicer 5.12.0 的 CMakeLists.txt 要求 `cmake_minimum_required(VERSION 3.28.0)`，而系统 yum 源仅提供 3.27.9。

修复方案（对应分析报告方向1）：
1. 将 `cmake` 从 `yum install` 列表中移除，同时添加 `wget` 用于下载
2. 新增从 `https://github.com/Kitware/CMake/releases/download/v3.28.6/` 下载 CMake 3.28.6 的预编译 Linux 二进制包
3. 根据 Docker `TARGETARCH` 选择正确的架构：`arm64` → `aarch64`，其他 → `x86_64`
4. 解压到 `/usr/local`（使用 `--strip-components=1`），使 `cmake` 等二进制位于 `/usr/local/bin/`（已在 PATH 中）

**验证结果**：已从 GitHub API 确认 CMake v3.28.6 Release 包含以下 Linux 二进制包：
- `cmake-3.28.6-linux-x86_64.tar.gz`（对应 amd64）
- `cmake-3.28.6-linux-aarch64.tar.gz`（对应 arm64）

两个架构的二进制包均可正常下载。

## 潜在风险
- CMake 3.28.6 从 GitHub Releases 下载依赖网络可达性，若 GitHub 不可达则构建会失败（与 yum 源不可达的风险相当）
- CMake 3.28.6 可能对 CTKAppLauncher 和 TBB 的构建产生行为差异，但从经验看新版本 CMake 向后兼容性好，且这两个组件的 CMake 要求较低，风险很低