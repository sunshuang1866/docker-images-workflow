# 修复摘要

## 修复的问题
`install.sh` 脚本无法移除 dnf 安装的 RPM 包管理型 npm，导致 Docker 构建在 "removing existing npm" 步骤失败。

## 修改的文件
- `Others/npm/11.13.0/24.03-lts-sp4/Dockerfile`: 将 `curl -qL https://www.npmjs.com/install.sh | sh` 替换为 `npm install -g npm@${VERSION}`

## 修复逻辑
分析报告指出根因是 `install.sh` 的 "移除已有 npm" 机制无法处理 RPM 包管理器安装的文件布局，导致移除失败。修复方案采用分析报告建议的"方向 1（置信度: 高）"：使用 `npm install -g npm@${VERSION}` 替代 `install.sh`。`npm install -g npm@...` 是 npm 内置的升级路径，能够正确处理由 dnf 安装的 npm 的升级，不会触发文件权限或布局冲突。同时，此修改使镜像实际安装的是 `${VERSION}` 指定的 11.13.0，而非 `install.sh` 默认安装的最新版（如 12.0.0），与目录命名保持一致。

## 潜在风险
无。`npm install -g npm@${VERSION}` 是该仓库其他 npm Dockerfile 未使用但 npm 官方推荐的升级方式，且 dnf 安装的 nodejs 已提供可用的 npm 运行时作为前置条件。