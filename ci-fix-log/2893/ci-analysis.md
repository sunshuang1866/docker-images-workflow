# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
- 失败位置: CI 运行时的 [Check] 测试阶段（非 Docker 构建阶段）
- 失败原因: CI 环境中缺少 `shunit2`（Shell 单元测试框架），测试脚本 `common_funs.sh` 在第 13 行尝试 `source shunit2` 时找不到该文件

### 与 PR 变更的关联

**与 PR 变更无关。** 证据如下：

1. Docker 镜像构建阶段完全成功（全部 422/422 编译目标通过，meson install 完成，镜像导出并推送成功）
2. 失败发生在构建完成后的 [Check] 测试验证阶段，该阶段由 CI 编排工具 `eulerpublisher` 触发
3. `shunit2` 是 CI runner 上的测试依赖，并非 Dockerfile 或镜像内需要安装的软件包
4. PR 变更仅涉及新增 Dockerfile、named.conf、README.md 表格条目、image-info.yml 表格条目、meta.yml 条目，均不涉及 CI 测试框架配置

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的构建节点上安装 `shunit2` 测试框架，使其对 `common_funs.sh` 中的 `source` 命令可见。这属于 CI 基础设施运维操作，Code Fixer 无需处理。

### 方向 2（置信度: 低）
如果 `shunit2` 是 `eulerpublisher` 包的自带依赖，可能是 `eulerpublisher` 安装不完整或版本升级后路径变化。检查 CI runner 上 `eulerpublisher` 包的完整性，确认 `shunit2` 文件是否存在于预期路径。

## 需要进一步确认的点
- CI runner 上 `shunit2` 的预期安装路径是什么？检查 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 或 eulerpublisher 的打包配置
- 该 CI 节点上的其他镜像（如相同基础镜像的其他 bind9 版本）的 [Check] 测试是否也失败？如果其他镜像也失败，则确认是 runner 环境问题
- `eulerpublisher` 包版本是否有变化？可能需要重新安装或修复依赖
