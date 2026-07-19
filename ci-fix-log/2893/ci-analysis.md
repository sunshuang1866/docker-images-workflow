# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架内部脚本）
- 失败原因: CI 的 `eulerpublisher` 测试框架在 [Check] 阶段执行容器镜像验证测试时，其公共脚本 `common_funs.sh` 尝试 `source shunit2`（shell 单元测试框架），但 CI runner 环境中未安装/未配置 `shunit2`，导致测试脚本无法启动。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，并更新了 meta.yml、README.md 和 image-info.yml 等元数据文件。

日志证据表明 PR 引入的 Dockerfile 构建完全成功：
- 编译阶段：全部 422/422 个目标编译通过，所有库和二进制文件成功链接
- 安装阶段：所有二进制、库、man 手册正常安装
- 构建阶段：Docker 镜像构建完成（`[Build] finished`）
- 推送阶段：镜像成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`（`[Push] finished`）

失败发生在构建和推送**之后**的 [Check] 阶段，由 CI 基础设施自身的测试框架依赖缺失导致，与本次 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 shell 脚本单元测试框架，通常可通过系统包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`），或从 GitHub Releases 下载后放置到 CI 测试脚本可访问的路径中。

## 需要进一步确认的点
- CI runner 镜像中是否本应预装 `shunit2` 但被意外移除/遗漏
- 同一 CI runner 上其他同类 PR（如其他新增 Dockerfile 的 PR）的 [Check] 阶段是否也出现相同错误
- `eulerpublisher` 测试框架是否有机制在测试前自动安装依赖（shunit2），如果有，该机制为何未生效
