# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 的 `[Check]` 阶段在执行测试脚本 `common_funs.sh` 时，第 13 行尝试引用/执行 `shunit2`（Shell 单元测试框架），但该工具未安装在 CI Runner 上，导致测试框架自身无法启动。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 Go 1.25.6 的 Dockerfile（`Others/go/1.25.6/24.03-lts-sp4/Dockerfile`）及配套的 README.md、image-info.yml、meta.yml 元数据更新。Docker 镜像构建和推送均已完成且成功（日志中所有 `#7`~`#11` 步骤均标记为 `DONE`，`[Build] finished` 和 `[Push] finished` 均正常输出）。`shunit2` 缺失是 CI Runner 环境问题，属于基础设施故障，与代码变更无任何因果关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner（构建节点）上安装 `shunit2` Shell 测试框架。这是 `eulerpublisher` 工具 `[Check]` 阶段的运行时依赖，`common_funs.sh` 在第 13 行需要 `source` 该库才能执行容器镜像的功能验证测试。安装后重新触发构建即可通过。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但未被 `common_funs.sh` 找到，需检查 CI Runner 上 `shunit2` 的安装路径是否在 `PATH` 环境变量中，或 `common_funs.sh` 中 source 路径是否正确。

## 需要进一步确认的点
- `shunit2` 是否应为 CI Runner 预装组件（需检查 CI 环境配置模板 / Ansible 剧本 / 容器编排定义）
- 该 CI Runner（`ecs-build-docker-aarch64-01-sp` 或同类 aarch64 节点）此前是否成功执行过其他镜像的 `[Check]` 测试——如果是，说明 `shunit2` 可能近期被移除或环境被意外破坏
- `common_funs.sh` 中 `shunit2` 的预期安装路径（如 `/usr/bin/shunit2`、`/usr/local/bin/shunit2` 或 `eulerpublisher` 内置路径）
