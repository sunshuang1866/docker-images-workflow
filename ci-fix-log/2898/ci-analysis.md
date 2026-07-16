# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 尝试引用 shell 单元测试框架 `shunit2`，但该工具在 CI runner 的 `PATH` 或预期路径中不存在，导致容器镜像健康检查测试（`test_go_version` 等）无法执行。

### 与 PR 变更的关联

**与 PR 无关。** 该 PR 的变更包括：
- 新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`（Go 1.25.6 + openEuler 24.03-LTS-SP4 基础镜像）
- 更新 `README.md`、`image-info.yml`、`meta.yml` 中的版本条目

Docker 镜像的构建（#7-#11）和推送已**完整成功**——日志中可见：
- `#7 DONE 67.8s`（Go 压缩包下载解压完成）
- `#8 DONE 40.5s`（文件时间戳与符号链接建立完成）
- `#9 DONE 1.5s`（构建依赖移除完成）
- `#11 exporting to image ... DONE 41.9s`（镜像导出、推送完成）
- `[Build] finished` / `[Push] finished`

失败仅发生在构建完成后的 [Check] 容器验证阶段，由 CI 测试框架的依赖缺失（`shunit2`）引起，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 构建 runner 上安装 `shunit2` 测试框架包，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 的第 13 行可以正确引用到 `shunit2`。对于 openEuler/CentOS 系环境，可通过包管理器安装：

```
dnf install shunit2
```

或将 `shunit2` 脚本放置在 `eulerpublisher` 测试框架的同级目录下。

## 需要进一步确认的点

- CI runner 环境中 `shunit2` 应当预装的位置和版本：是否有特定的 `eulerpublisher` 包版本与 `shunit2` 的捆绑关系？
- 该 [Check] 阶段是否为本次 SP4 平台新增，而相应的 CI 环境尚未配置 `shunit2` 依赖？
- 其他同类镜像（如已有的 `1.25.6-oe2403sp3`）的 [Check] 测试是否正常通过？若正常通过，则需对比两者 CI runner 的环境差异。
