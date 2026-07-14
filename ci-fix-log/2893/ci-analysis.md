# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在容器镜像的 `[Check]`（测试/校验）阶段执行 `common_funs.sh` 时，尝试通过 `.` (source) 命令加载 `shunit2` 测试框架，但该框架未安装或不在搜索路径中，导致 `[Check] test failed`。

关键：Docker 镜像的构建、安装和推送全部成功完成（步骤 `#9` ~ `#13` 均为 `DONE`，日志中明确输出 `[Build] finished` 和 `[Push] finished`），失败仅发生在 CI 自身对已构建镜像执行容器启动测试的校验阶段。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、配置文件 (`named.conf`) 及元数据条目，Docker 构建流程完全成功（meson 编译 422 个目标全部通过、镜像导出和推送均完成），失败完全由 CI 环境的 shunit2 依赖缺失引起。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，非代码层面可修复。需由 CI 运维人员检查 `eulerpublisher` 在 aarch64 runner 上的测试环境，确保 `shunit2` 已安装且位于 `eulerpublisher/tests/container/common/` 目录或其搜索路径中。Code Fixer 无需操作。

## 需要进一步确认的点
- CI runner（aarch64）上 `shunit2` 是否已安装、安装路径是否与 `common_funs.sh` 中引用的路径一致
- 其他镜像（非 bind9）在同类 runner 上是否也出现相同的 `[Check] test failed` 错误，以确认是本次构建节点的特有问题还是该 runner 类型的系统性问题
