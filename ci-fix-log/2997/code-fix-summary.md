# 修复摘要

## 修复的问题
无需代码修改 — 此为基础设施错误（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 失败原因为 CESM 的 `checkout_externals` 脚本在构建中调用 `svn checkout` 从外部 SVN 服务器 `svn-ccsm-models.cgd.ucar.edu` 拉取 `chem_proc` 组件时，SVN 服务器的 SSL 证书与当前主机名不匹配（`certificate issued for a different hostname`），导致 TLS 握手被拒。

此失败与 PR #2997 的代码变更无关，是 NCAR/UCAR 外部 SVN 服务器的 SSL 证书配置问题。PR 的 Dockerfile 及所有变更文件本身无任何错误，前置依赖安装步骤（yum、mpich、hdf5、netcdf、pnetcdf）均成功完成。

该问题需要：
- NCAR/UCAR 修复其 SVN 服务器的 SSL 证书；或
- CI 基础设施管理员协调处理构建环境的证书信任问题。

## 潜在风险
无（未修改任何代码）