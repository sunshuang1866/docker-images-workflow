# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书验证失败
- 新模式症状关键词: svn, E230001, Server SSL certificate verification failed, certificate issued for a different hostname, checkout_externals

## 根因分析

### 直接错误
```
#16 90.96 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 92.39 ERROR:root:Failed with output:
#16 92.39     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 92.39     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
```

### 根因定位
- 失败位置: `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile:52-55`（`./manage_externals/checkout_externals` 步骤）
- 失败原因: CESM 的 `manage_externals/checkout_externals` 工具在校验 cam 组件的外部依赖时，尝试通过 SVN 从 `svn-ccsm-models.cgd.ucar.edu` checkout `chem_proc5_0_04`，但该 SVN 服务器的 SSL 证书与访问的主机名不匹配，导致 SVN 客户端拒绝连接。所有前置依赖（mpich、hdf5、netcdf-c、netcdf-fortran、pnetcdf）及 yum 包安装均成功完成。

### 与 PR 变更的关联
此失败与 PR 的代码变更**无直接关联**。PR 仅新增了一个 Dockerfile 和 `config_compilers.xml` 配置文件，Dockerfile 中引用的 `checkout_externals` 命令本身是正确的 CESM 标准构建流程。失败根因在于上游 UCAR SVN 服务器的 SSL 证书配置问题，属于 CI 基础设施或上游服务侧的问题。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `checkout_externals` 执行前，通过 `svn` 配置或环境变量跳过 SSL 证书主机名校验。例如，在 `RUN` 命令中预先执行 `svn --non-interactive --trust-server-cert-failures=cn-mismatch` 对目标 SVN URL 的 info 操作，或设置 `~/.subversion/servers` 中对应 host 的 `ssl-trust-default-ca` 为 `yes`。注意：此方法会降低 SSL 安全级别，仅适用于受信任的内部构建环境。

### 方向 2（置信度: 中）
检查 CESM 上游仓库的 `Externals_CAM.cfg` 配置文件中 `chem_proc` 的 SVN URL。`svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书可能已更新或因服务器迁移改变了主机名映射。如果上游已有针对 CESM 2.2.2 的新版 externals 配置，可考虑在 build 前 `sed` 更新 Externals 配置文件中的 URL。

### 方向 3（置信度: 低）
如果该 SVN 服务器长期不可达，可考虑在 Dockerfile 中手动 clone/git 替代 chem_proc 源码（若存在对应的 GitHub 镜像），但需要确认版本一致性。

## 需要进一步确认的点
1. `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书当前状态——是临时性问题还是已永久变更，可通过在本地执行 `openssl s_client -connect svn-ccsm-models.cgd.ucar.edu:443` 确认证书 CN/SAN。
2. CESM 2.2.2 的 `Externals_CAM.cfg` 中 chem_proc 的 SVN URL 是否已有上游更新（对比 `release-cesm2.2.2` tag 与最新 main 分支的 externals 配置）。
3. 其他 CESM 版本的 Dockerfile（如同目录下其他 OS 版本）是否也存在相同的 SVN 问题——若是，说明这是通用上游变更而非本 PR 特有问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无。本问题不涉及对第三方源文件的正则 patch 操作。
