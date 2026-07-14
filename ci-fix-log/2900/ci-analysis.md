# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: "测试框架缺失"
- 新模式症状关键词: `shunit2`, `file not found`, `Check test failed`, `common_funs.sh`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI 流程的 `[Check]` 阶段（`eulerpublisher` 容器测试框架）
- 失败原因: 测试框架 `eulerpublisher` 的公共函数脚本 `common_funs.sh` 第 13 行尝试 source `shunit2`，但 `shunit2` 文件在 `$PATH` 或测试目录中不存在，导致测试套件无法加载，所有检查项均为空，判定为 test failed。

### 与 PR 变更的关联

**与本次 PR 变更无关。** PR 的改动为新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 构建阶段（源码编译、make、make install、配置 sed 修改、镜像构建和推送）全部成功完成：

- `#10 DONE 41.6s` — httpd 编译和安装完成
- `#11 DONE 0.1s` — 用户创建和配置修改完成
- `#14 exporting to image` — 镜像导出成功
- `#14 pushing manifest` — 镜像推送成功

失败发生在构建之后的 `[Check]` 测试阶段，且错误原因是 CI 测试框架自身的依赖 `shunit2` 缺失，属于 CI 基础设施问题，与 PR 代码质量无关。

## 修复方向

### 方向 1（置信度: 中）
CI 运行环境缺少 `shunit2`（shUnit2，一种 Shell 单元测试框架）。需要在 CI runner 的测试环境镜像中安装 `shunit2`，或确保 `eulerpublisher` 测试框架的依赖（如 `shunit2` 包）已预装在执行 `[Check]` 阶段的容器/环境中。openEuler 上可通过 `yum install shunit2` 或 `dnf install shunit2` 安装。

### 方向 2（置信度: 低）
如果 `shunit2` 并非系统包而是作为脚本文件随 `eulerpublisher` 分发，可能是 `eulerpublisher` 的包版本或安装路径存在问题，导致 `shunit2` 文件未被部署到预期的搜索路径中。

## 需要进一步确认的点

1. 该 CI runner 上其他同类型 PR 的 `[Check]` 阶段是否也因同样原因失败（确认是否为此 runner 的持久问题）
2. `shunit2` 在该 openEuler 24.03-LTS-SP4 runner 环境中是否可通过包管理器安装，还是需要以其他方式部署
3. `eulerpublisher` 测试框架的完整依赖列表和安装文档，确认 `shunit2` 的预期来源和路径配置
