# 1024test：部署能力考核项目

这是一个故意保持很小的 Python + MySQL 项目。学生要完成的重点是从 Windows 命令行获取源码、打包并传到 Ubuntu，在 Ubuntu 上配置数据库和虚拟环境，再用 systemd 部署并在重启后验证功能。`test_部署验收清单.md` 是逐项验收记录。

## 学生任务

1. 在 Windows 上用 Git 命令行从教师提供的 GitHub 仓库克隆项目，检查文件，并打成 zip。通过 `scp` 上传到 Ubuntu；全程只用命令行和 SSH，不用图形化文件管理器，也不下载仓库 zip。
2. 在 Ubuntu 建立 `/home/test`，将 zip **直接解压到该目录**。验收时应存在 `/home/test/requirements.txt`、`/home/test/.env.example`、`/home/test/schema.sql`，而不是 `/home/test/1024test/` 等额外层级。复制 `.env.example` 为 `.env` 后编辑。
3. 安装 Python、venv、pip、MySQL、vim 和解压工具。以 MySQL root 身份创建 `1024test` 库、`accounts` 表，以及 MySQL 用户 `test`。该用户对 `1024test` 库**只能拥有 SELECT、INSERT、UPDATE、DELETE 权限**，不能有建表、删表或全局权限。`schema.sql` 给出了库表结构；建用户和授权由学生完成。
4. 在 `/home/test` 建 Python 虚拟环境，从 `requirements.txt` 安装所有依赖。用 vim 修改 `.env` 中的数据库连接信息。数据库密码不得提交到公开仓库。
5. 先在前台启动 `1024test-server` 验证可以运行，然后配置 `deployment/1024test.service`，由 systemd 托管、后台持续运行并开机自启。服务应以普通 Ubuntu 用户运行。把虚拟环境中的 `1024test` 命令安装到 PATH，使任何目录都可执行。
6. 重启虚拟机后执行下面的功能验收。调试纠错最多 **10 次**，每次修改后重新验证，并在清单记录次数。
7. 在 Ubuntu 上把项目提交并推送到自己的 GitHub 仓库；访问受限时可用 Gitee。公开仓库中不能包含已填写密码的 `.env`、`.venv`、数据库转储或打包文件，并展示仓库内容。

## 验收命令与预期

在 Ubuntu 的任意目录执行命令。配置文件由 systemd 服务从 `/home/test/.env` 读取。客户端默认连接本机 8024 端口；若修改了 `APP_PORT`，需设置环境变量 `TEST1024_ENV=/home/test/.env`。

| 顺序 | 操作 | 预期 |
| --- | --- | --- |
| 1 | 重启 Ubuntu，检查 systemd 服务状态 | 服务处于 active，enabled |
| 2 | `1024test -m user 123456` | 标准输出 `true` |
| 3 | `1024test -l user` | 显示 `password：`，输入 `123456` 后输出 `logining` |
| 4 | MySQL root 执行 `DELETE FROM \`1024test\`.accounts WHERE username='user';` | 删除 1 行 |
| 5 | 重启服务，再执行 `1024test -l user` | 输出 `无该用户` |
| 6 | 停止服务，执行 `1024test -v` | 提示无法执行，退出码非 0 |

`-m` 使用命令行密码是为了匹配原始考核要求；实际业务系统通常不应在命令行参数中传密码，因为它可能被进程列表或终端历史记录看到。此项目只绑定 `127.0.0.1`，供单机部署练习。

## 配置说明

- `.env.example` 已包含端口和账户占位配置；学生须复制为 `.env`，再使用 vim 填写 `DB_PASSWORD`。实际密码只留在 Ubuntu 虚拟机中，`.env` 已列入 `.gitignore`。
- `schema.sql` 只做建库、建表和一条幂等的初始配置写入，必须由 MySQL root 运行。文件中没有创建 MySQL 用户、设置密码或 `GRANT` 语句；`test` 用户和授权必须由学生手动完成。服务的 `test` 用户不会执行 DDL。
- `deployment/1024test.service` 中的 `REPLACE_WITH_UBUNTU_USERNAME` 必须替换为实际普通用户。确保该用户能读取 `/home/test/.env` 和项目文件。
- `requirements.txt` 同时安装 PyMySQL 和本地项目，所以安装后虚拟环境中会有 `1024test`、`1024test-server` 两个命令。不要使用 `1024test-server --help` 检查安装；服务端命令没有帮助模式，会按配置启动服务。可用 `pip show test1024` 或检查虚拟环境的命令文件确认安装。
- 推荐创建 PATH 中的启动包装器，内容执行 `/home/test/.venv/bin/1024test "$@"`。如更改了服务端口，再将 `TEST1024_ENV` 指向 `/home/test/.env`。包装器的文件权限应允许普通用户执行。

## 教师验收要点

| 考点 | 应查看的证据 |
| --- | --- |
| Git 与打包传输 | Windows 的 clone、zip、scp 命令记录；Ubuntu 中解压目录结构 |
| 环境与依赖 | Ubuntu 软件包、虚拟环境、`pip list` 与项目命令 |
| MySQL 最小权限 | `SHOW GRANTS FOR 'test'@'localhost';`，库表存在，应用以该账号连接 |
| 配置与调试 | vim 操作、`.env` 值、纠错记录不超过 10 次 |
| systemd | unit 文件、`systemctl is-enabled`、重启后 `systemctl is-active` |
| 功能与持久化 | 上表所有输出；root 删除后重启服务依然无用户；停服务后命令失败 |
| 代码托管 | Ubuntu 上的 git push 记录、学生仓库页面、无密码泄漏 |

## 本地开发验证

无需 MySQL 即可运行协议和命令行测试：`python -m unittest discover -s tests -v`。完整部署验收必须在 Ubuntu + MySQL + systemd 环境进行。
