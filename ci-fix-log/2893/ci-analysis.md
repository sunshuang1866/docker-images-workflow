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
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的 `eulerpublisher` 测试基础设施 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段执行容器镜像测试时，`common_funs.sh` 脚本尝试通过 `.` (source) 命令加载 `shunit2` Shell 单元测试框架，但 `shunit2` 文件在 CI Runner 的预期路径中不存在，导致测试套件无法启动。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 named.conf 配置）、更新了 README.md 和 image-info.yml（追加新版本表格行）、更新了 meta.yml（追加新版本路径映射）。Docker 镜像的构建（全部 422 个编译单元 + 链接 + meson install）和推送均已成功完成，失败发生在 CI 编排工具 `eulerpublisher` 的后置检查阶段，属于 CI Runner 环境缺少测试依赖的问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` Shell 单元测试框架，确保 `/usr/local/etc/eulerpublisher/tests/` 目录或其 `PATH` 搜索路径中可找到 `shunit2` 文件。这不是 Dockerfile 或代码层面的问题，需由 CI 基础设施维护者处理。

## 需要进一步确认的点
- CI Runner 环境中 `shunit2` 本应存在于哪个路径（如 `/usr/local/share/shunit2/shunit2` 或 `/usr/lib/shunit2`），以及为何本次 Runner 实例中缺失。
- 确认同一镜像的其他版本（如 `9.21.23-oe2403sp3`）在相同的 CI 环境下是否能通过 [Check] 阶段，以区分是全局 Runner 环境问题还是本次调度异常。
