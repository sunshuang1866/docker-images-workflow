# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 [Check] 阶段在执行 `common_funs.sh` 脚本时尝试引用 `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 上，导致测试脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增 Go 1.25.6 的 openEuler 24.03-LTS-SP4 Dockerfile 并更新了 3 个元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建完全成功，日志明确显示：

- 镜像下载解压阶段成功：`#7 DONE 67.8s`
- 文件修改和符号链接阶段成功：`#8 DONE 40.5s`
- 构建工具清理阶段成功：`#9 DONE 1.5s`
- 镜像导出和推送成功：`[Build] finished` / `[Push] finished`
- 镜像推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64` 成功

失败仅发生在构建后的 [Check] 测试阶段，`shunit2` 缺失是 CI 基础设施环境问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。需联系 CI 基础设施管理员在 runner 镜像中补充 `shunit2` 包，或确认 `common_funs.sh` 脚本对 `shunit2` 的路径引用是否正确（文件可能被误删或路径变更）。

### 方向 2（置信度: 低）
若 `shunit2` 是 `eulerpublisher` 的依赖但未随包安装，可检查 `eulerpublisher` 包的安装完整性，确认 `pip install` 或相关依赖安装步骤是否遗漏了 `shunit2`。

## 需要进一步确认的点
- `shunit2` 是否为 `eulerpublisher` 包的已声明依赖，还是作为系统级工具单独安装的。
- CI runner 的镜像模板近期是否有变更（如 `shunit2` 被意外移除）。
- 是否有其他近期 PR（使用同一 runner）同样出现此问题，以确认是 runner 级别还是特定触发条件的问题。
