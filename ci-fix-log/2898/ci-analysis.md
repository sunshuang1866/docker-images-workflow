# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 测试基础设施 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段（镜像构建后验证）依赖 `shunit2` Shell 单元测试框架，但 `common_funs.sh` 脚本执行 `. shunit2` 时该文件在 CI runner 上不存在，导致测试框架载入失败，整体检查阶段报 `[Check] test failed`。

### 与 PR 变更的关联
**与 PR 变更完全无关。** PR 新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（纯新增 34 行）、README.md 文档记录，以及 `meta.yml` 注册条目。Docker 镜像的构建（5/5 步骤全部 DONE）、推送（Push finished）均成功完成，构建过程无任何错误。失败仅发生在构建完成后的 CI 测试基础设施（`[Check]` 阶段），该阶段属于 CI 平台运维范畴，非 PR 代码可控制。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，无需修改 PR 代码。CI 管理员需要在 CI runner 上安装 `shunit2` Shell 测试框架（或确保 `common_funs.sh` 的 `PATH` 中包含 `shunit2` 脚本路径）。建议对照同仓库其他测试脚本（如 `tests/faiss/faiss_test.sh`、`tests/protobuf/protobuf_test.sh`）中已有的 `download_shunit2()` 函数，在 `common_funs.sh` 中也加入从 GitHub/镜像站动态下载 shunit2 的兜底逻辑，避免对 runner 预装依赖的硬性要求。

## 需要进一步确认的点
- 确认同一 CI runner 上其他 Go 版本镜像（如 `1.25.6-oe2403sp3`）的 [Check] 步骤是否也因 `shunit2` 缺失而失败，还是仅本次运行受影响
- 确认 `common_funs.sh:13` 是否预期从某个固定路径（如 `/usr/local/bin/shunit2`）或相对路径（如 `./shunit2`）source 该文件，以确定 CI runner 的修复方式

## 修复验证要求
不适用 — 此失败为 CI 基础设施问题，PR 代码无需修改。
