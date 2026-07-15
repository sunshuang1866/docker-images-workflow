# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用，与已有模式39高度相似)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 框架测试脚本）
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器镜像测试时，`common_funs.sh` 脚本尝试 source `shunit2` 测试框架库，但 shunit2 未安装在当前 CI runner（aarch64）上，导致测试脚本无法运行。Docker 镜像的构建（422 个编译单元全部通过）和推送（`[Push] finished`）均已成功完成。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（45 行）、named.conf（14 行）及对应的 README、image-info.yml、meta.yml 条目。Docker 构建阶段全部成功：
- 编译：422/422 目标全部完成（含 libisc、libdns、libns、libisccc、libisccfg 等库及 named 等可执行文件）
- 安装：`meson install` 成功将二进制安装到 /usr/lib64、/usr/bin、/usr/sbin
- 镜像构建：Docker build 6 个步骤均成功，镜像导出并推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`

失败发生在 CI 自身的 [Check] 测试阶段，属于 CI 基础设施问题，与本次 PR 代码完全无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner（aarch64 节点）缺少 `shunit2` shell 测试框架。需运维在 aarch64 CI runner 上安装 `shunit2` 包（可通过 `yum install shunit2` 或等效方式），或检查 `eulerpublisher` 框架中 `common_funs.sh` 的 shunit2 引用路径是否正确（如是否需要将 `shunit2` 置于 `PATH` 内或指定绝对路径）。

### 方向 2（置信度: 中）
若 shunit2 已在 runner 上安装但路径未被脚本发现，可检查 `common_funs.sh` 中第 13 行的 `source` 命令写法，确认是否遗漏了 shunit2 的安装路径前缀（如 `/usr/share/shunit2/shunit2`）。

## 需要进一步确认的点
- 确认当前 aarch64 CI runner 上是否已安装 `shunit2` 包（`rpm -qa | grep shunit2` 或 `which shunit2`）
- 确认同一 PR 的 x86_64 (amd64) 架构构建 job 是否也遇到相同的 `shunit2: file not found` 错误，还是已成功通过 [Check] 阶段
- 若 amd64 构建也失败，则问题可能影响所有架构；若仅 aarch64 失败，则可能仅该架构的 runner 缺少 shunit2
- 检查模式39 的历史案例修复方式是否适用（PR #2894 `Others/bisheng-jdk/README.md` 中同为 eulerpublisher 工具依赖缺失的 infra-error）

## 修复验证要求
此失败为 infra-error，不涉及代码修复。Code-fixer 无需对 Dockerfile 或任何 PR 文件进行修改。若需重新触发 CI，需先确认 runner 上 `shunit2` 的可用性。
