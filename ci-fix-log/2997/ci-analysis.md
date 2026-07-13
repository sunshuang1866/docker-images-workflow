# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书不匹配
- 新模式症状关键词: svn, E230001, Server SSL certificate verification failed, certificate issued for a different hostname, checkout_externals

## 根因分析

### 直接错误
```
#16 90.96 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 92.39 ERROR:root:Failed with output:
#16 92.39     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 92.39     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
#16 ERROR: process "/bin/sh -c yum install -y subversion cmake lapack-devel blas-devel perl-XML-LibXML && git clone -b release-cesm${VERSION} https://github.com/ESCOMP/cesm.git cesm2 && cd cesm2 && ./manage_externals/checkout_externals" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile:52-55`（`./manage_externals/checkout_externals` 步骤）
- 失败原因: CESM 的 `manage_externals/checkout_externals` 脚本通过 `svn checkout` 从 UCAR 服务器 `svn-ccsm-models.cgd.ucar.edu` 拉取 `chem_proc`（chem_proc5_0_04）外部依赖时，SVN 客户端检测到该服务器 SSL 证书中的 hostname 与实际访问的 hostname 不一致，SSL 验证失败。这与 Dockerfile 代码逻辑无关。

### 与 PR 变更的关联
此次 PR 是新增 Dockerfile，代码逻辑本身无错误。前期步骤（yum 安装依赖、编译 MPICH/HDF5/NetCDF/PNetCDF、git clone CESM 仓库）均成功完成。失败发生在外部的 SVN 服务器 SSL 证书问题，属于 CI 基础设施/网络环境问题，非 PR 代码缺陷。

上游 UCAR 的 SVN 服务器 `svn-ccsm-models.cgd.ucar.edu` 提供的 SSL 证书可能因 CDN/代理/负载均衡导致 hostname 不匹配，或该域名近期更换了托管服务器导致证书尚未更新。

## 修复方向

### 方向 1（置信度: 中）
在运行 `./manage_externals/checkout_externals` 之前，通过 SVN 配置关闭该特定主机的 SSL 证书验证。在 Dockerfile 的 RUN 命令中添加：
```
mkdir -p ~/.subversion && echo '[global]' > ~/.subversion/servers && echo 'ssl-verify=false' >> ~/.subversion/servers
```
注意：此方法降低了安全性，仅适用于构建环境。

### 方向 2（置信度: 中）
重试构建。如果 SSL 证书问题是 UCAR 服务器侧的临时性问题（如证书刚更新、DNS 缓存未同步），在数小时/数天后重试 CI 可能自动通过。建议先确认是否为临时性问题。

### 方向 3（置信度: 低）
在 SVN checkout 命令层面使用 `--trust-server-cert-failures=cn-mismatch` 参数。但 CESM 的 `checkout_externals` 脚本内部调用 SVN，不直接暴露 SVN 参数，需要在 CESM 的 `manage_externals` 工具源码中找到 SVN 调用点并添加该参数，维护成本较高。

## 需要进一步确认的点
1. UCAR 服务器 `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书是否确实已过期或 hostname 不匹配（可通过 `openssl s_client -connect svn-ccsm-models.cgd.ucar.edu:443 -servername svn-ccsm-models.cgd.ucar.edu` 从 CI runner 网络环境验证）
2. 在其他平台（如 24.03-lts-sp3、22.03-lts-sp4）上构建 CESM 2.2.2 时是否遇到同样错误（即判断是否为 openEuler 24.03-LTS-SP4 容器镜像中 CA 证书包的问题）
3. 该 SVN 服务器历史上是否稳定可用，或者这是首次在该 CI 环境中访问该 SVN 服务器
