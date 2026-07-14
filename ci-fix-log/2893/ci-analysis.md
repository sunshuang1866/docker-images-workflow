# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段执行容器镜像功能测试时，`common_funs.sh` 尝试 source `shunit2`，但该 Shell 测试框架未安装在当前 CI runner 上，导致测试脚本启动失败。

### 关键证据：构建与推送均成功
日志显示 Docker 镜像的编译、链接、安装、推送全部成功完成：

- `#9 DONE 41.4s` — meson 编译（422/422 编译目标全部完成）、链接、安装成功
- `#10 DONE 0.2s` — groupadd/useradd 命令正常执行
- `#12 DONE 0.1s` — 文件权限设置正常
- `#13 DONE 36.0s` — 镜像导出并推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功
- 2026-07-10 09:23:59,481 — `[Build] finished` 和 `[Push] finished` 日志均已输出

失败仅发生在 build + push 之后的 [Check] 容器测试阶段，与本文 PR 的 Dockerfile、named.conf 或元数据文件变更均无关。

### 与 PR 变更的关联
PR 变更内容全部正确，与失败无关：

| 文件 | 变更 | 与失败的关联 |
|------|------|-------------|
| `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile` | 新增 Dockerfile | 构建阶段全部成功，无关联 |
| `Others/bind9/9.21.23/24.03-lts-sp4/named.conf` | 新增配置文件 | 仅在 COPY 步骤使用，步骤 #11 成功 |
| `Others/bind9/README.md` | 新增表格行 | 纯文档，无关联 |
| `Others/bind9/doc/image-info.yml` | 新增表格行 | 纯文档，无关联 |
| `Others/bind9/meta.yml` | 新增 tag 映射条目 | 元数据正确，构建调度正常 |

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 节点上安装 `shunit2` Shell 测试框架。该框架是 `eulerpublisher` 容器测试基础设施的前置依赖，缺失后会导致所有容器镜像的 [Check] 阶段失败。可在 CI 环境中通过 `yum install shunit2` 或等效方式安装。

## 需要进一步确认的点
- 确认当前 CI runner 节点（`ecs-build-docker-aarch64-*` 系列）上 `shunit2` 的安装状态。若该节点上其他 PR 的 [Check] 阶段也同时失败，则进一步确认为 CI 基础设施问题。
- 确认 `shunit2` 在 openEuler 仓库中的包名（可能为 `shunit2` 或 `shunit`），以及是否需要在 CI runner 初始化脚本中添加安装步骤。

## 修复验证要求
无需代码修复。若 CI 运维侧安装 shunit2 后，应重新触发 PR #2893 的 CI 流水线，验证 [Check] 阶段能正常完成容器的启动与功能测试。
