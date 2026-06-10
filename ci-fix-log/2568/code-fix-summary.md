# 修复摘要

## 修复的问题
版本号 `-26-05-1-1` 的前导连字符 `-` 导致 CI 系统构造出非法的 Docker image tag（以 `-` 开头），`docker buildx` 拒绝该引用格式。

## 修改的文件
- `Others/slurm/meta.yml`: 将 key `-26-05-1-1-oe2403sp3` 改为 `26-05-1-1-oe2403sp3`，path 中的 `-26-05-1-1/` 改为 `26-05-1-1/`
- `Others/slurm/README.md`: 将 tag 和链接中的 `-26-05-1-1-oe2403sp3` 改为 `26-05-1-1-oe2403sp3`，目录路径同步更新
- `Others/slurm/doc/image-info.yml`: 同上，将 tag 和链接中的 `-26-05-1-1` 改为 `26-05-1-1`
- `Others/slurm/-26-05-1-1/` 目录重命名为 `Others/slurm/26-05-1-1/`（移除前导连字符）

## 修复逻辑
CI 的 eulerpublisher 工具从目录层级中提取版本号并拼接 Docker image tag。目录名 `-26-05-1-1` 以 `-` 开头，导致最终 tag 为 `-26-05-1-1-oe2403sp3`，违反 Docker tag 命名规范（只能以字母数字或下划线开头）。移除版本号前导 `-` 后，生成的 tag `26-05-1-1-oe2403sp3` 符合 Docker 规范。

## 潜在风险
无。版本号的前导 `-` 没有语义含义（其他 Slurm 版本目录如 `25.11.6.1/` 均不以 `-` 开头），移除后不影响任何功能。Dockerfile 内容未做修改（内部 `ARG TAG=slurm-25-11-6-1` 不受影响）。