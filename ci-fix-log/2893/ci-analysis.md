# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失，变体）
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的通用测试脚本 `common_funs.sh` 第 13 行通过 `. shunit2` 尝试加载 shell 单元测试库 `shunit2`，但该库在 CI runner 环境中未安装或不在 `PATH` 中，导致 `[Check]` 阶段在尚未实际执行容器功能测试前即崩溃退出。

### 与 PR 变更的关联
**无关**。PR 变更仅为新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf、meta.yml 和文档条目。CI 日志明确显示：

1. Docker 构建成功——bind9 全部 422 个编译单元编译通过，所有二进制文件安装完毕（`#9 DONE 41.4s`）
2. 镜像 push 成功——`[Build] finished` + `[Push] finished`
3. 失败仅发生在 `[Check]` 阶段，且在运行**任何容器测试之前**即因 `shunit2: file not found` 而终止

该错误是 CI runner 自身测试环境缺少依赖（`shunit2`）导致的基础设施问题，PR 的任何改动均不可能引发此错误。

## 修复方向

### 方向 1（置信度: 高）
CI 运维在相关 runner（aarch64 构建节点及对应的 test runner）上安装 `shunit2` shell 单元测试框架（如通过 `dnf install shunit2` 或等效方式），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中 `. shunit2` 能正常解析。

## 需要进一步确认的点
- 该 CI runner 上此前是否有其他镜像构建成功通过 `[Check]` 阶段？若此前均正常，可能是 runner 环境近期被变更导致 `shunit2` 被移除。
- 由于日志中仅包含 aarch64 架构的构建输出（镜像 tag 为 `-aarch64`），需确认 x86-64 架构的构建是否也因相同原因失败，或已有其他独立错误。

## 修复验证要求
（不适用——此为 infra-error，无需 code-fixer 介入）
