# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, Check, test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 的测试框架 `eulerpublisher` 在 [Check] 阶段执行容器启动验证测试时，依赖的 `shunit2` shell 测试库在该 aarch64 Runner 上未安装/不可用，导致 `common_funs.sh` 第 13 行的 `. shunit2` source 命令失败。

### 与 PR 变更的关联
**无关**。本次 PR 的 Docker 镜像构建阶段完全成功：
- Docker 构建所有 422 个 C 编译目标均通过，libisc/libdns/libns/libisccc/libisccfg 全部链接成功
- `meson install` 将所有二进制/mon page 安装至 `/usr`，`#9 DONE 41.4s`
- 镜像导出和推送均成功：`#13 exporting manifest list ... done`，`[Build] finished`，`[Push] finished`
- 镜像已成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败发生在 CI 自身的 [Check] 阶段——`eulerpublisher` 工具尝试对已构建好的镜像运行容器启动测试，但其依赖的测试库 `shunit2` 在 CI Runner 上缺失。这是 CI 基础设施配置问题，与本次 PR 的 Dockerfile、named.conf、meta.yml 等变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 aarch64 CI Runner 上安装 `shunit2`。`shunit2` 是一个标准的 shell 单元测试框架，通常可通过包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`），或从 GitHub 获取后置于测试框架的 `$PATH` 中。此修复在 CI 基础设施侧进行，无需修改 PR 中的任何文件。

## 需要进一步确认的点
- 当前日志仅展示 aarch64 构建 job 的输出，需确认 amd64 构建 job（x86-64 runner）的 [Check] 测试是否也因同样原因失败，还是已成功通过。
- 确认该 aarch64 CI Runner 上 `shunit2` 是否曾可用但因环境变更被移除，还是从未安装过。
- 确认其他在同一 CI Runner 上构建的镜像（如 bind9 的其他 Tag）的 [Check] 测试是否也出现了相同的 `shunit2: file not found` 错误——如果有，说明这是一个已有的 CI 基础设施问题；如果没有，需进一步排查 Runner 差异。
