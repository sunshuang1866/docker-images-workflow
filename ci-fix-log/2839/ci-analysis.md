# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 环境（`eulerpublisher` Check 阶段）
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架，`common_funs.sh` 在第 13 行尝试加载 `shunit2` 时失败，导致镜像验证测试无法执行，Check 表格结果为空，整个构建被标记为失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅涉及新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 条目和 README 文档。Docker 镜像的构建阶段（`make -j $(nproc) && make install`）和推送阶段均成功完成：
- 构建成功：`#8 DONE 268.4s`（PostgreSQL 从源码编译完成并安装到 `/usr/local/pgsql`）
- 推送成功：`#11 DONE 58.0s`（镜像 `17.6-oe2403sp4-x86_64` 已推送至 registry）

失败仅发生在 `eulerpublisher` 的 `[Check]` 后处理阶段，根因是 CI runner 缺少 `shunit2` 测试依赖，属于 CI 基础设施配置问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境（或 `eulerpublisher` 安装脚本）中补充安装 `shunit2` 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行可以成功加载 `shunit2`。`shunit2` 可通过各发行版的包管理器安装（如 `dnf install shunit2` 或从 GitHub 克隆安装）。

### 方向 2（置信度: 低）
如果 `shunit2` 实际已安装但路径不在 `PATH` 环境变量中，则需要检查 CI runner 的 `PATH` 配置或修改 `common_funs.sh` 的加载方式以使用绝对路径。

## 需要进一步确认的点
1. CI runner 上 `shunit2` 是否已安装：通过 `which shunit2` 或 `shunit2 --version` 验证
2. 其他同类 PR（其他数据库镜像的新增）在 Check 阶段是否也遇到相同的 `shunit2` 缺失问题——如果是，则确认为 CI runner 全局基础设施问题
3. 如果不是全局问题，需要确认是否为该特定 runner 节点（ecs-build-docker-x86-64-xx）的环境配置遗漏
