# 修复摘要

## 修复的问题
Dockerfile 中 COPY 脚本后未赋予执行权限，导致 RUN 执行脚本时报 Permission denied (exit code 126)。

## 修改的文件
- `HPC/3dslicer/5.10.0/24.03-lts-sp3/Dockerfile`: 在 COPY 三个 .sh 脚本之后、WORKDIR/RUN 之前，新增 `RUN chmod +x /opt/build-CTKAppLauncher.sh /opt/build-tbb.sh /opt/build-Slicer.sh` 为脚本赋予执行权限。

## 修复逻辑
CI 分析报告指出根因是 Dockerfile 通过 COPY 将三个构建脚本复制到容器后，未执行 chmod +x 赋予执行权限，导致 `./build-CTKAppLauncher.sh` 直接运行时 Permission denied。添加一行 chmod +x 即可解决，且改动最小。

## 潜在风险
无