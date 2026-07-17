# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」同类，但缺失组件不同）
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, Check test failed, eulerpublisher

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架）
- 失败原因: `eulerpublisher` 工具在 [Check] 阶段对已构建的镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 执行检查时，其测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2`（Bash 单元测试框架），但该文件在 CI runner 上不存在，导致测试框架初始化失败，整个构建流程被标记为 FAILURE。

### Docker 镜像构建和推送均成功
日志中 Docker build 的 5 个步骤（Step 1/5 至 5/5）全部执行成功（`DONE`），镜像导出、推送也全部完成（`[Build] finished`、`[Push] finished`）。失败仅发生在构建完成后的 [Check] 测试阶段，该阶段由 `eulerpublisher` 编排工具驱动，与 Dockerfile 中定义的镜像内容无关。

### 与 PR 变更的关联
**无关**。PR 变更仅涉及：
- 新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`（Go 1.25.6 镜像定义）
- 更新 `Others/go/README.md`（文档表格新增一行）
- 更新 `Others/go/doc/image-info.yml`（元数据表格新增一行）
- 更新 `Others/go/meta.yml`（新增版本条目）

这些变更属于标准的新镜像版本添加操作，不涉及 CI 测试框架、`shunit2` 安装脚本或测试配置文件。`shunit2` 是 CI runner 环境上的工具依赖，PR 代码无法影响其可用性。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2`（Bash 单元测试框架）。`shunit2` 通常可通过系统包管理器（`dnf install shunit2`）或从 GitHub releases 获取。安装后确认路径 `/usr/share/shunit2/shunit2` 或 `/usr/local/bin/shunit2` 可被 `common_funs.sh` 的 source 语句正确引用。

### 方向 2（置信度: 低）
如果 `shunit2` 实际已安装但路径不正确，检查 `common_funs.sh` 第 13 行的 source 路径配置是否需要调整为 CI runner 上的实际 `shunit2` 安装路径。

## 需要进一步确认的点
- 确认该 CI runner 节点之前是否成功执行过其他镜像的 [Check] 阶段。如果之前也失败，则 `shunit2` 为全局缺失；如果仅本次失败，可能是该 runner 为新建/重建节点、环境未完整初始化。
- 检查 `common_funs.sh` 的 source 语句期望的 `shunit2` 路径是多少，确认是否与系统实际安装路径一致。
