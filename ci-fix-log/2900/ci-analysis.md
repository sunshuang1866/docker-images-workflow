# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
#14 exporting to image
#14 pushing layers 15.8s done
#14 pushing manifest for docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64@sha256:b38237a0854eb058b77e7e857d62923d7166fbe49740c2ce2f0206f7e858ea4b
#14 DONE 31.3s

2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），导致 `common_funs.sh` 在执行 `. shunit2` 时找不到该文件，[Check] 阶段测试无法运行，直接返回 CRITICAL 失败

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像构建和推送均成功完成（[Build] finished、[Push] finished），所有 7 个 RUN 步骤全部通过。失败发生在 CI 测试框架自身的初始化阶段——`shunit2` 框架文件在 CI runner 上不可用，导致容器镜像的 [Check] 测试连一个检查项都未能执行（检查结果表为空）。PR 新增的 Dockerfile、httpd-foreground 脚本及元数据文件均未涉及 CI 测试框架的配置。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2` 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正确 source 该文件。这属于 CI 基础设施维护问题，与 PR 代码无关，Code Fixer 无需对本仓库做任何修改。

### 方向 2（置信度: 低）
若 `shunit2` 本应安装在 CI runner 上且其他同类镜像的 [Check] 均通过，可能是本次 CI 运行的环境异常（runner 临时故障或镜像回退导致 shunit2 丢失）。可尝试重新触发 CI 运行验证是否为临时性 infra 问题。

## 需要进一步确认的点
1. 确认其他近期成功的 httpd 镜像 PR（如 `2.4.66-oe2403sp2`）是否在相同 CI runner 上通过 [Check] 阶段——若也失败，则为全局 infra 问题；若通过，则可能是本次调度到的特定 runner 故障
2. 确认 CI 测试框架 `eulerpublisher` 对 `shunit2` 的依赖方式：是系统级安装、pip 依赖还是内嵌文件
3. 确认 `shunit2` 在该 CI runner 路径下是否曾被手动安装后因 runner 重建而丢失
