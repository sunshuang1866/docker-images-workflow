# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `Check test failed`

## 根因分析

### 直接错误
```
[Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的 `eulerpublisher` 测试框架层
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 在第 13 行尝试 `source shunit2`，但 `shunit2` 壳层单元测试框架未安装在 CI Runner 上，导致测试无法执行，Check 步骤失败。（Build 和 Push 阶段均已成功完成并推送镜像。）

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 构建（`#10 DONE 41.6s`）、配置步骤（`#11 DONE 0.1s`）和镜像推送（`#14 DONE 31.3s`）全部成功。失败发生在 CI 平台的 Check 后验证阶段，原因是 Runner 缺少 `shunit2` 测试工具——这是 CI 基础设施配置问题，与 Dockerfile、README、meta.yml 等代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 运维方在 Runner 上安装 `shunit2` 壳层测试框架。shunit2 是开源项目（https://github.com/kward/shunit2），需确保其安装路径在 `PATH` 中或 `common_funs.sh` 可正确 source 到。此问题无法通过修改 Dockerfile 或仓库代码解决，需 CI 平台侧介入。

## 需要进一步确认的点
- 确认 shunit2 应该安装的路径（`common_funs.sh:13` 的 source 路径是相对路径还是绝对路径，是否依赖特定安装位置）
- 确认是否只有特定 Runner（如 x86_64）缺少 shunit2，而其他架构 Runner 正常
- 排查是否是 Runner 镜像更新后 shunit2 被移除

## 修复验证要求
不适用（infra-error，非代码修复范畴）。若 CI 运维侧安装 shunit2 后重跑，需确认 `[Check]` 测试表中有实际测试项和执行结果输出。
