# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
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
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试环境中缺少 `shunit2` Shell 单元测试框架，`common_funs.sh` 脚本在第 13 行执行 `. shunit2` 时找不到该文件，导致 Check 阶段立即退出，所有容器测试用例均未能执行。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅为新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 启动脚本及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送均已成功完成：

- `#10 DONE 41.6s` — `make && make install` 成功
- `#11 DONE 0.1s` — 用户创建和配置修改成功
- `#14 DONE 31.3s` — 镜像导出和推送成功
- `[Build] finished` / `[Push] finished`

失败发生在 CI 编排工具 `eulerpublisher` 的容器检查（Check）阶段，该阶段依赖宿主机上的 `shunit2` 测试框架，与 PR 中提交的任何文件均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2`（可通过 `dnf install shunit2` 或 `git clone https://github.com/kward/shunit2.git` 后配置 PATH），确保测试框架对 Check 阶段可用。此问题属于 CI 基础设施配置缺失，非 Dockerfile 或代码层面的问题。

### 方向 2（置信度: 低）
若 `shunit2` 原本存在于 CI 环境中但被意外移除，则需排查 CI runner 的依赖管理流程（如最近的基础镜像更新是否误删了该包）。

## 需要进一步确认的点
- CI runner 的基础环境中是否预期包含 `shunit2`——若是，需确认本次构建使用的 runner 实例为何缺失该包。
- `eulerpublisher` 的 Check 阶段是否最近有更新，导致 `shunit2` 的期望安装位置发生变化（`common_funs.sh` 中 `. shunit2` 未指定绝对路径，依赖 PATH 或同目录下存在该文件）。
