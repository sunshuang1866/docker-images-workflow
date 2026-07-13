# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SVN证书主机名不匹配
- 新模式症状关键词: svn, E230001, certificate issued for a different hostname, checkout_externals, chem_proc

## 根因分析

### 直接错误
```
#16 52.69 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 53.67 ERROR:root:Failed with output:
#16 53.67     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 53.67     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
#16 ERROR: process "/bin/sh -c yum install -y subversion cmake lapack-devel blas-devel perl-XML-LibXML && ... &&     cd cesm2 &&     ./manage_externals/checkout_externals" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile 第 52-57 行 RUN 指令中的 `./manage_externals/checkout_externals` 步骤，具体在 checkout `chem_proc` 子组件时
- 失败原因: CESM 的 `manage_externals/checkout_externals` 脚本内部通过 `svn checkout` 从 `svn-ccsm-models.cgd.ucar.edu` 拉取 `chem_proc` 组件，该 SVN 服务器的 TLS 证书与访问主机名 `svn-ccsm-models.cgd.ucar.edu` 不匹配，SVN 客户端拒绝连接。CI 日志显示 RUN 命令中已尝试通过 `ssl-trust-default-ca = yes` 配置 `/root/.subversion/servers` 来放宽验证（该配置不在 PR diff 中，疑似 CI 流水线自动注入），但该选项只解决 CA 信任链问题，无法解决主机名不匹配（hostname mismatch）问题，因此仍然失败。

### 与 PR 变更的关联
- PR 为 CESM 2.2.2 新增了 openEuler 24.03-LTS-SP4 的 Dockerfile（全新文件），Dockerfile 中的 `./manage_externals/checkout_externals` 步骤是 CESM 官方构建流程的一部分。
- 该失败并非 PR 代码变更引入的 bug，而是 CESM 上游依赖的 SVN 服务器 SSL 证书配置问题。但该问题在构建此新 Dockerfile 时暴露，需要工作绕过。
- 该失败与所依赖的第三方基础设施（UCAR SVN 服务器）的证书配置有关，任何尝试通过 `svn` 从此服务器拉取代码的环境都会复现此问题。

## 修复方向

### 方向 1（置信度: 高）
在 `./manage_externals/checkout_externals` 执行前，配置 SVN 全局忽略证书主机名不匹配错误。在 PR diff 中现有的 RUN 命令内（`git clone` 之后、`./manage_externals/checkout_externals` 之前），追加配置 `/root/.subversion/servers` 文件的 `[global]` 段，添加 `trust-server-cert-failures = unknown-ca,cn-mismatch,expired,not-yet-valid,other`。该选项是 SVN 1.9+ 提供的细粒度证书忽略机制，可覆盖主机名不匹配场景（`cn-mismatch`）。

具体位置：Dockerfile 第 52-57 行 RUN 命令中，`git clone ...` 与 `./manage_externals/checkout_externals` 之间，补充一行 `printf 'trust-server-cert-failures = unknown-ca,cn-mismatch,expired,not-yet-valid,other\n' >> /root/.subversion/servers`。

注意：CI 日志中的实际执行命令已包含 `mkdir -p /root/.subversion && printf '[global]\nssl-trust-default-ca = yes\n' > /root/.subversion/servers`，但 PR diff 的 Dockerfile 中不包含这些行。修复时需一并确保 `mkdir -p /root/.subversion` 和完整的 `servers` 文件配置（`[global]` 段 + `ssl-trust-default-ca` + `trust-server-cert-failures`）全部包含在 RUN 命令中。

## 需要进一步确认的点
- 确认 `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书问题是否为临时性故障（可通过直接 curl/wget 该 URL 验证）。如果是临时性故障，上述 SVN 配置绕过方案作为保底工作区仍有价值。
- 确认目标 openEuler 24.03-LTS-SP4 镜像中的 SVN 版本（即 `subversion` RPM 包版本）是否 >= 1.9.0（`trust-server-cert-failures` 选项需要 SVN >= 1.9）。从日志中安装的 `subversion-1.14.3` 来看满足要求。
- 确认 CESM 2.2.2 的 `chem_proc` 组件是否已从 SVN 迁移到其他版本控制系统（如 Git），如果是，则更彻底的修复是调整 `Externals_CAM.cfg` 或使用更新的 CESM release tag。

## 修复验证要求
- code-fixer 在提交前，需确认修改后的 RUN 命令（含 `printf 'trust-server-cert-failures = ...' >> /root/.subversion/servers`）在 openEuler 24.03-LTS-SP4 容器环境中能成功完成 `./manage_externals/checkout_externals` 步骤。
- 如果上游 SVN 服务器 SSL 证书已修复，验证 Dockerfile 在不添加 `trust-server-cert-failures` 的情况下是否也能通过构建（作为可选后备方案）。
