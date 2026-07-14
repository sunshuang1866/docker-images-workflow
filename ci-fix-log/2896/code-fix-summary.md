# 修复摘要

## 修复的问题
openEuler 24.03-lts-sp4 基础镜像缺少 `shadow` 包导致 `groupadd`/`useradd` 命令找不到（exit code 127），同时修正 README.md 和 image-info.yml 中错误的版本描述文案（22.03-LTS-SP4 → 24.03-LTS-SP4）。

## 修改的文件
- `Others/dotnet-deps/8.0/24.03-lts-sp4/Dockerfile`: 在 `yum install` 列表中添加 `shadow` 包，并移除无效的 `rm -rf /var/lib/apt/lists/*`（该命令为 Debian/Ubuntu 系容器专用，在 openEuler 中无实际作用）。
- `Others/dotnet-deps/README.md`: 将 `8.0-oe2403sp4` 的描述从 "openEuler 22.03-LTS-SP4" 修正为 "openEuler 24.03-LTS-SP4"。
- `Others/dotnet-deps/doc/image-info.yml`: 同上，将 `8.0-oe2403sp4` 的描述从 "openEuler 22.03-LTS-SP4" 修正为 "openEuler 24.03-LTS-SP4"。

## 修复逻辑
1. **`shadow` 包缺失**：openEuler 24.03 系列基础镜像默认不预装 `shadow` 包（提供 `groupadd`/`useradd` 命令），导致 Dockerfile 第 21-22 行执行时命令找不到。在 `yum install` 列表中添加 `shadow` 即可解决。这是 openEuler 24.03 系列的已知特征（CI 分析报告模式05）。
2. **无效清理命令**：`rm -rf /var/lib/apt/lists/*` 是 Debian/Ubuntu 系容器清理 APT 缓存的惯用写法，在 openEuler（使用 yum/dnf）中不存在该目录，该命令无实际作用，属于从其他 Dockerfile 错误移植的冗余代码，移除后由 `yum clean all` 覆盖清理逻辑。
3. **文案错误**：README.md 和 image-info.yml 中将基于 `24.03-lts-sp4` 的镜像描述为 "22.03-LTS-SP4"，属于复制粘贴错误，修正为正确的版本号。

## 潜在风险
无。`shadow` 包是 openEuler 官方仓库提供的标准包，与已有依赖无冲突；文案修正仅涉及描述性文字，不影响构建或运行。