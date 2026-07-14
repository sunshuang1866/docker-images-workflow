# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 运行环境中未安装 `shunit2`（Shell 单元测试框架），导致容器镜像构建完成后的 [Check] 验证阶段脚本（`common_funs.sh`）执行失败。Docker 镜像的编译、链接（全部 422 个目标）、安装和推送均已成功完成。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`（含 bind9 的 yum 依赖安装、meson 编译构建）、`named.conf` 配置文件，以及 `README.md`、`image-info.yml`、`meta.yml` 的文档/元数据更新。日志显示 Docker 构建全流程成功（`#9 DONE 41.4s`、`#10 DONE 0.2s` 至 `#12 DONE 0.1s`，镜像已成功导出并推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`），失败仅发生在构建完成后的 CI 自身测试框架初始化阶段。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` 包。`shunit2` 是 Shell 脚本的单元测试框架，eulerpublisher 的容器检查脚本 `common_funs.sh` 依赖它来执行容器启动验证测试。确保 `shunit2` 可被 source 加载（如在 `/usr/share/shunit2/shunit2` 或 PATH 可搜索路径中），使 `common_funs.sh:13` 的 `. shunit2` 命令能正常执行。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 是否曾安装但因系统升级/清理被移除
- 确认 `eulerpublisher` 容器测试框架（`tests/container/common/common_funs.sh`）是否依赖特定版本的 `shunit2`
- 确认该问题是否仅影响新增镜像的 check 阶段，还是影响所有使用 `common_funs.sh` 的容器镜像检查——如果是后者，则属于 CI 基础设施的全局问题

## 修复验证要求
无（此类 infra-error 的修复需由 CI 运维团队在 runner 节点上进行，Code Fixer 无法通过修改 Dockerfile 或仓库文件解决）。
