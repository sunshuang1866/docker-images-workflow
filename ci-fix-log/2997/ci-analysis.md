# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书不匹配
- 新模式症状关键词: svn, E230001, SSL certificate verification failed, certificate issued for a different hostname

## 根因分析

### 直接错误
```
#16 90.96 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 92.39 ERROR:root:Failed with output:
#16 92.39     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 92.39     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
#16 ERROR: process "/bin/sh -c ... ./manage_externals/checkout_externals" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile:52-55`（`./manage_externals/checkout_externals` 步骤）
- 失败原因: CESM 的 `manage_externals/checkout_externals` 工具在检出外部依赖 `chem_proc` 时，通过 `svn checkout` 连接 NCAR/UCAR 的 SVN 服务器 `svn-ccsm-models.cgd.ucar.edu`，该服务器返回的 SSL 证书与请求的 hostname 不匹配，SVN 客户端拒绝连接。所有前置依赖编译（mpich、hdf5、netcdf-c、netcdf-fortran、pnetcdf）均构建成功，失败仅发生在 CESM 自身源码的外部依赖拉取阶段。

### 与 PR 变更的关联
- **PR 变更直接触发了该失败**。本次 PR 新增了 CESM 2.2.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中第 52–55 行的 `./manage_externals/checkout_externals` 命令是 CESM 官方构建流程的标准步骤。该步骤在 Docker 构建环境中调用 SVN 访问 NCAR 外部仓库时因 SSL 证书校验失败。
- 这不是 PR 引入的逻辑错误，而是外部依赖服务（`svn-ccsm-models.cgd.ucar.edu`）的 SSL 证书配置问题与构建环境 SVN 客户端严格校验之间的冲突。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中 `./manage_externals/checkout_externals` 执行之前，配置 SVN 全局选项以信任目标服务器的 SSL 证书（绕过 hostname 不匹配的校验）。在 `/root/.subversion/servers` 文件中为 `svn-ccsm-models.cgd.ucar.edu` 所在域配置 `ssl-trust-default-ca = yes` 或等效的 `ssl-verify-server-cert = no`，使 `checkout_externals` 调用的 `svn checkout` 能够接受不匹配的证书。

### 方向 2（置信度: 中）
使用 `--non-interactive --trust-server-cert-failures=unknown-ca,cn-mismatch,expired,not-yet-valid,other` 等效配置。如果 `manage_externals` 不支持传递自定义 SVN 参数，可在 Dockerfile 中将 `svn` 包装为 shell 函数或替换 `svn` 二进制路径，在 `checkout_externals` 调用之前通过 `alias` 或 PATH 注入带默认信任参数的 wrapper。

## 需要进一步确认的点
- 确认 `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书 hostname 不匹配是否为长期问题还是临时配置异常。若为临时问题可等待上游恢复，若为长期问题则需引入上述绕过方案。
- 确认 CESM 是否有其他同类 Dockerfile（如其他 OS 版本）使用相同流程且已通过 CI，其是否也遇到同样的 SVN SSL 问题。
- 确认 `manage_externals/checkout_externals` 工具是否支持通过环境变量或配置文件自定义 SVN 参数（如 `SVN_OPTIONS`、`~/.subversion/config` 等）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。
