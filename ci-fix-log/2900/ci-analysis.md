# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 宿主机 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境的 `eulerpublisher` 测试框架脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试框架），但该文件在 CI Runner 上不存在，导致 `[Check]` 阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建阶段（Build/Push）已完全成功：
- configure → make → make install 全部通过（`#10 DONE 41.6s`）
- 所有 7 个 Dockerfile 步骤均成功执行
- 镜像已成功构建并推送到 registry（`#14 DONE 31.3s`）
- `[Build] finished` 和 `[Push] finished` 均正常完成

失败仅发生在构建完成后的 `[Check]` 测试阶段，原因是 CI Runner 缺少 `shunit2` 测试依赖，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
该失败为 CI 基础设施问题，无需修改 PR 代码。需要在 CI Runner 上安装 `shunit2`（Shell 单元测试框架），或修复 `eulerpublisher` 测试框架的依赖路径配置，确保 `common_funs.sh` 第 13 行能正确找到 `shunit2` 文件。

## 需要进一步确认的点
- 确认 CI Runner 环境中 `shunit2` 的预期安装路径（是否应通过 `rpm` 包安装，还是通过环境变量 `SHUNIT2_HOME` 指定）
- 检查同类 PR 的 CI 运行日志，确认 `[Check]` 步骤在其他成功的镜像构建中是否也会执行 `shunit2`（若均跳过或均失败，说明这是一个已知的系统性问题）

## 修复验证要求
无需验证（故障与 PR 代码变更无关，属于 CI 基础设施问题）。
