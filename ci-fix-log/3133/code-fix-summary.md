# 修复摘要

## 修复的问题
Dockerfile 中 `pip install mindspore==2.3.0rc1` 失败，因基础镜像 `openeuler/cann:8.0.RC1-oe2203sp4` 内置 pip 源仅提供 `mindspore==2.0.0`。

## 修改的文件
- `AI/mindspore/2.3.0rc1-cann8.0.RC1/24.03-lts-sp4/Dockerfile`: 在 `pip install` 命令中添加 `--index-url https://pypi.org/simple/`，使 pip 从 PyPI 获取 `mindspore==2.3.0rc1`

## 修复逻辑
CI 失败分析报告指出根因是基础镜像的 pip 源中 mindspore 最高版本仅 2.0.0，远低于 PR 要求的 2.3.0rc1。按照分析报告方向 1（高置信度），在 pip install 命令前添加 `--index-url` 指向 PyPI，绕过基础镜像自带的受限 pip 仓库。MindSpore 从 2.3.0 起使用统一包名，PyPI 上的 `mindspore` 包支持 CPU/GPU/Ascend 多后端，与 CANN 基础镜像兼容。

## 潜在风险
- 若 PyPI 不可达（网络问题），构建会失败。可考虑替换为 `https://pypi.tuna.tsinghua.edu.cn/simple` 等国内镜像作为备选。
- 安装的 mindspore 版本来自 PyPI 而非 CANN 基础镜像配套仓库，需确认其与 CANN 8.0.RC1 运行时兼容。