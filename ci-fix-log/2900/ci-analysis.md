# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
#14 exporting to image
#14 pushing layers 15.8s done
#14 pushing manifest ... done
#14 DONE 31.3s

[Build] finished
[Push] finished
[Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
CRITICAL: [Check] test failed

+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 流水线 [Check] 阶段 — `common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` Shell 单元测试框架，导致 `eulerpublisher` 的容器镜像验证脚本无法执行测试，[Check] 阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成（`#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`），PR 中新增的 Dockerfile、httpd-foreground 脚本、meta.yml 配置均无问题。失败发生在 CI 自身的容器验证（Check）阶段，原因是指定 Runner 上未安装 `shunit2` 测试框架，属于 CI 基础设施配置问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 包。openEuler 环境中可通过 `dnf install shunit2` 安装该 Shell 单元测试框架，确保 `eulerpublisher` 的 Check 步骤能正常执行容器启动验证。

### 方向 2（置信度: 低）
如果 CI Runner 无法安装 `shunit2`，可在 CI 流水线中为当前 Runner 节点添加 `shunit2` 的手动部署步骤（如将 `shunit2` 脚本拷贝到 Runner 的 PATH 路径中）。

## 需要进一步确认的点
- 本次 CI 运行使用的 Runner 节点标签/名称，确认该节点的软件预装清单中是否确实缺失 `shunit2`。
- 是否为该 Runner 节点首次运行 httpd 类镜像的 Check 验证，或是否此前该节点曾成功执行过 `shunit2` 测试。
- 下游架构专属构建 job（如 aarch64）的日志是否需要一并获取，以排除多架构并行构建中其他 job 的失败可能。
