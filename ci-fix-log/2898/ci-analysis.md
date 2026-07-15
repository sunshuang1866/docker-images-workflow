# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 主机 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在执行 `[Check]` 阶段时，测试公共函数脚本 `common_funs.sh` 尝试加载 `shunit2` 测试框架，但该框架未安装在 CI Runner 上，导致测试初始化失败。

### 与 PR 变更的关联
**无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（新文件）及配套的元数据更新（README.md、image-info.yml、meta.yml），未改动任何 CI 基础设施配置。Docker 镜像构建（步骤 #7 至 #11）和推送（`[Push] finished`）均成功完成，失败仅发生在构建后的 `[Check]` 测试阶段，且失败原因是 CI Runner 上缺少 `shunit2` 命令。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架。该框架通常可通过系统包管理器安装（如 `apt install shunit2` 或 `dnf install shunit2`），或从 GitHub Release 下载。安装后重新触发 CI 构建，预期 `[Check]` 阶段可通过。

### 方向 2（置信度: 低）
若 CI Runner 环境不可更改（如共享 Runner），可考虑在 Dockerfile 中内置 `shunit2`，将测试脚本修改为从容器内运行。但从当前日志看，测试脚本位于 CI Runner 主机路径 `/usr/local/etc/eulerpublisher/tests/`，此方向可能涉及 CI 工具 `eulerpublisher` 自身的改动，非本仓库范畴。

## 需要进一步确认的点
1. 确认 CI Runner 的操作系统及包管理器，以确定 `shunit2` 的正确安装命令。
2. 确认 `shunit2` 在 CI 环境中的预期安装路径（`common_funs.sh` 中 `source` 或 `.` 命令引用的具体路径）。
3. 确认其它同类 PR（如其他应用镜像的新增 Dockerfile）的 `[Check]` 阶段是否也因同样原因失败，以判断这是否是新增 Runner 或新 OS 版本触发的系统性基础设施问题。
