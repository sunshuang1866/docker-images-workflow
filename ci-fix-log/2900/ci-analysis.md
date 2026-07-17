# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 的 `[Check]` 测试阶段执行容器健康检查脚本时，`common_funs.sh` 第 13 行 `source shunit2` 失败——CI runner 环境中未安装 `shunit2` 测试框架，导致 Check 步骤无法运行任何测试用例（测试结果表为空），直接报 `CRITICAL` 退出。Docker 镜像的构建（Build）和推送（Push）阶段均正常完成。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile (`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`) 在所有 Docker 构建步骤均成功完成（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`），镜像已成功构建并推送到注册表（`exporting manifest list sha256:b38237...` done，`pushing layers 15.8s done`）。失败仅发生在 `eulerpublisher` 工具的 `[Check]` 后验证阶段，属于 CI runner 基础设施依赖缺失问题。

## 修复方向

### 方向 1（置信度: 低）
在 CI runner 环境中安装 `shunit2` 测试框架。该错误 `shunit2: file not found` 表明测试环境缺少 shunit2 包（openEuler 中可能为 `shunit2` 或 `shunit` RPM 包），需运维人员在执行检查的 CI 节点上安装该依赖。

注：此为 infra 修复，Code Fixer 无需处理 PR 代码。

## 需要进一步确认的点
1. 同一 CI runner 上其他已成功通过 `[Check]` 阶段的镜像（如 `httpd:2.4.66-oe2403sp2`）是否使用了相同的 `common_funs.sh` 脚本，如果是，则排除脚本路径问题，确认为该特定 runner 节点缺少 `shunit2`。
2. CI 平台是否使用了多架构 runner（x86_64 vs aarch64），不同架构节点的 `shunit2` 安装状态可能不同。
3. `common_funs.sh` 中 `source shunit2` 调用是否依赖于某个特定的 `PATH` 或 `SHUNIT2_HOME` 环境变量设置，该变量在当前 runner 上可能未配置。
