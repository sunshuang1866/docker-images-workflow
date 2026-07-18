# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, line 13, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 基础设施 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: aarch64 CI runner 上缺少 `shunit2` 包（shell 单元测试框架），导致 `[Check]` 阶段脚本中 `source shunit2` 失败。Docker 镜像构建和推送均已成功完成（422/422 编译通过、`meson install` 成功、`#13 exporting to image` 完成），失败仅发生在 CI 后处理/测试验证阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 named.conf 配置）及更新 README、image-info.yml、meta.yml 等元数据文件。Docker 构建阶段完全通过，失败发生在 `eulerpublisher` 工具的 `[Check]` 流水线阶段——该阶段依赖的 `shunit2` 测试框架未在 CI runner 上安装，属于纯基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**CI 运维在 aarch64 runner 上安装 `shunit2` 包。** CI 的 `[Check]` 阶段脚本 `common_funs.sh` 第 13 行执行 `. shunit2` 试图加载 shunit2 测试框架但文件不存在。需在对应 runner 上通过包管理器安装 `shunit2`（openEuler 上可用 `dnf install shunit2`）。

### 方向 2（置信度: 低）
若 `shunit2` 包名因系统版本不同而有所差异，需检查 runner 的 openEuler 版本并确认正确的包名（如某些系统中可能是 `shunit2`、`shunit` 等不同命名）。

## 需要进一步确认的点
- 确认 aarch64 CI runner 上 `shunit2` 的实际包名及安装状态（`dnf list installed | grep shunit`）
- 确认同一镜像的其他架构（如 amd64）是否也因相同原因失败，还是 amd64 runner 上 shunit2 已安装成功
- 检查 `common_funs.sh` 脚本的内容，确认 `shunit2` 的 source 路径是否需要根据 openEuler 的实际安装路径调整

## 修复验证要求
本次无需 code-fixer 修改代码，需 CI 运维验证 aarch64 runner 上安装 `shunit2` 后重新触发 PR #2893 的 CI 流水线可正常通过。
