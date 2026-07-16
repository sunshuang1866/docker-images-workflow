# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 容器检查框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 宿主机 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 `[Check]` 阶段运行容器验证测试时，测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2` Shell 单元测试框架，但该框架未安装在当前 CI runner 环境中，导致测试流程崩溃。

### 与 PR 变更的关联
**无关联。** 该 PR 新增的 PostgreSQL 17.6 / openEuler 24.03-LTS-SP4 Docker 镜像构建完全成功（`make -j "$(nproc)" && make install` 无编译错误，镜像构建和推送均已完成）：

- `#8 DONE 268.4s` — 编译安装全部通过
- `#11 exporting to image ... DONE 58.0s` — 镜像构建与推送成功
- `[Build] finished` + `[Push] finished` — 构建和推送阶段均正常退出

失败仅发生在构建完成后的 `[Check]` 验证阶段，原因是 CI runner 环境缺少 `shunit2` 测试框架，与 Dockerfile、entrypoint.sh 或 meta.yml 的变更无关。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施修复**：在 CI runner 上安装 `shunit2` Shell 测试框架。`shunit2` 是 `eulerpublisher` 容器验证流程的运行时依赖，需确保 `common_funs.sh` 能成功 `source` 该框架。

## 需要进一步确认的点
- 确认 `shunit2` 是否应为 CI runner 镜像的预装依赖（与 eulerpublisher 打包在一起），还是当前 runner 因环境漂移丢失了该依赖。
- 确认同一 CI 流水线中其他同类 PR 的 `[Check]` 阶段是否也出现了相同错误，以判断是否为近期 CI 环境变更导致的全局性问题。
