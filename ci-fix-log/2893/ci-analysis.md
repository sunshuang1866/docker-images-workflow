# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的容器测试框架（`eulerpublisher`）在执行 [Check] 阶段的 shell 测试脚本 `common_funs.sh` 时，尝试用 `.` (source) 命令加载 `shunit2` 测试框架，但该框架在 CI runner 上未安装/未配置到 PATH，导致 `shunit2: file not found`，测试被标记为失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Docker 镜像的构建（`meson compile` 422/422 个目标全部编译成功）和推送（`[Push] finished`）均已成功完成。失败发生在构建/推送之后的 [Check] 阶段，根因是 CI runner 缺少 `shunit2` Shell 测试框架，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 节点上安装 `shunit2` 包。在 openEuler 上可通过 `dnf install shunit2` 安装。若 shunit2 已安装但不在 `common_funs.sh` 的预期路径，需修正该脚本中 `shunit2` 的引用路径。

## 需要进一步确认的点
- 确认 CI runner 节点（执行 `aarch64` 构建的节点）上 `shunit2` 包是否已安装（`dnf list installed shunit2` 或 `which shunit2`）
- 若 `shunit2` 已安装，确认 `common_funs.sh` 中对 `shunit2` 的引用路径是否正确（例如是否配置了 `PATH` 或使用了绝对路径）
- 确认同一镜像的其他架构构建 job（如 x86_64）是否也因同样原因失败
