# CI 失败分析报告

## 基本信息
- PR: #2941 — chore(npm): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 系统包管理器冲突
- 新模式症状关键词: removing existing npm, failed!, install.sh, dnf-installed npm

## 根因分析

### 直接错误
```
#8 [3/3] RUN curl -qL https://www.npmjs.com/install.sh | sh
#8 134.7 fetching: https://registry.npmjs.org/npm/-/npm-12.0.0.tgz
#8 151.4 removing existing npm
#8 151.8 failed!
#8 ERROR: process "/bin/sh -c curl -qL https://www.npmjs.com/install.sh | sh" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/npm/11.13.0/24.03-lts-sp4/Dockerfile:11`
- 失败原因: `npmjs.com/install.sh` 脚本尝试移除系统中已有的 npm（由 `dnf install nodejs` 安装的 RPM 版本 10.8.2），但该 npm 是由系统包管理器（RPM/dnf）管理的文件，install.sh 无权或无法正确移除这些文件，导致 "removing existing npm" 步骤失败。

构建流程为：
1. `dnf install nodejs -y` 从 openEuler 仓库安装了 nodejs 20.18.2，连带安装了 npm 10.8.2（RPM 包管理）
2. `curl -qL https://www.npmjs.com/install.sh | sh` 下载了 npm 12.0.0，然后尝试移除旧版 npm
3. install.sh 的"移除已有 npm"机制无法处理 RPM 包管理器安装的文件布局，移除失败

### 与 PR 变更的关联
**直接关联。** 该 PR 新增的 Dockerfile 在逻辑上存在冲突：先用 `dnf install nodejs` 安装系统级 npm，再用 `install.sh` 升级 npm。`install.sh` 并非设计用于覆盖 RPM 包管理器管理的安装。此 Dockerfile 只在新 PR 中引入，失败是由 PR 变更直接触发的。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中的两步安装合并为单一路径：要么只通过 dnf 安装 nodejs/npm（使用系统打包版本），要么只通过 `install.sh` 安装 npm（在安装 npm 之前，需要先单独安装 nodejs 运行时而不带 npm）。如果目标是安装特定版本的 npm（如 11.13.0），应使用 `npm install -g npm@${VERSION}` 而非 `install.sh`，因为前者能正确处理由 dnf 安装的 npm 的升级路径。

### 方向 2（置信度: 中）
如果必须使用 `install.sh`，则在调用 `install.sh` 之前先通过 `dnf remove npm -y` 移除 RPM 安装的 npm 包，确保 `install.sh` 不会遇到系统包管理器残留文件。但需注意 `dnf remove npm` 可能因依赖关系将 nodejs 也一并移除。

## 需要进一步确认的点
- 同级目录下 `Others/npm/11.13.0/24.03-lts-sp3/Dockerfile` 是否使用了相同的 `install.sh` 模式，还是使用了不同的 npm 升级方案。若 SP3 版本也用了同样方式且构建成功，则需对比 SP3 和 SP4 基础镜像中 dnf 安装的 npm 版本差异以定位根因差异。
