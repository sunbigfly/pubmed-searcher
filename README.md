# PubMed 搜索网页

## 项目简介
该项目是一个用于搜索和显示 PubMed 文章的工具。用户可以通过输入查询条件进行搜索，并对搜索结果进行操作，如收藏、标记已读、分享等。

## 目录结构

```
.
├── app.py                  # 应用的主文件
├── config.py               # 配置文件
├── extensions.py           # Flask 扩展初始化
├── forms.py                # 表单类定义
├── models.py               # 数据库模型定义
├── requirements.txt        # 项目依赖
├── static/                 # 静态文件目录
├── templates/              # HTML 模板目录
├── tmp/                    # 临时文件夹
├── journal_data_2024.json  # JSON 数据文件
├── getpubmedinfo.py        # PubMed 数据获取脚本
```

## 功能介绍

### 主要功能

- **搜索功能**：用户可以通过输入开始时间、截止时间、搜索结果数和搜索关键字进行搜索。
- **结果展示**：搜索结果以表格形式展示，用户可以查看每条结果的详细信息。
- **用户面板**：显示当前登录用户的信息，并提供退出登录的功能。
- **操作按钮**：
  - 前进：浏览器前进功能。
  - 后退：浏览器后退功能。
  - 搜索历史：查看之前的搜索历史。
  - 刚刚搜索：展示刚刚搜索的结果。
  - 加/进入收藏：将文章加入收藏或查看收藏的文章。
  - 加/进入已读：将文章标记为已读或查看已读的文章。
  - 加/进入喜闻乐见：将文章分享给所有人或查看所有人分享的文章。
  - 加/进入组会分享：将文章分享用于组会讨论或查看组会分享的文章。
  - 全选：选择所有搜索结果。
  - 全不选：取消选择所有搜索结果。
  - 反选：反选当前选择的搜索结果。
  - 删除：删除所选的搜索结果或收藏的文章等。

### 其他功能

- **返回顶部**：当页面向下滚动时，显示返回顶部按钮，点击后返回页面顶部。
- **动态排序**：根据当前页面的不同，动态设置表格的排序列和排序方式。
- **本地存储**：记住用户选择的按钮状态，本地存储激活的按钮，刷新页面后保持状态。

## 使用说明

### 运行项目

1. **安装 Conda**：如果你还没有安装 Conda，可以从 [Conda 官网](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) 下载并安装。

2. **创建 Conda 环境**：在项目根目录下运行以下命令创建一个新的 Conda 环境：

   ```bash
   conda create --name pubmed_search python=3.9
   ```

   这里我们创建了一个名为 `pubmed_search` 的环境，并指定了 Python 版本为 3.9。你可以根据需要调整 Python 版本。

3. **激活 Conda 环境**：激活刚刚创建的 Conda 环境：

   ```bash
   conda activate pubmed_search
   ```

4. **安装依赖**：在激活的 Conda 环境中，使用 `pip` 安装项目依赖：

   ```bash
   pip install -r requirements.txt
   ```

5. **设置环境变量**：根据 `config.py` 中的配置，设置必要的环境变量。你可以通过在命令行中导出环境变量，或者创建一个 `.env` 文件来设置这些变量。

6. **运行应用**：在开发环境中，你可以直接运行 `app.py`：

   ```bash
   python app.py
   ```
   > getpubmedinfo.py 里的 Entrez.email 与 Entrez.api_key 需要自己配置，不然Pubmed Fetch 的请求API 速率受限
   

   或者使用 Flask 提供的命令：

   ```bash
   flask run
   ```

7. **使用 Gunicorn 部署**：在生产环境中使用 Gunicorn，可以运行以下命令：

   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

   这将使用 4 个工作进程在端口 8000 上运行你的应用。


### 使用页面

![image](https://github.com/sunbigfly/pubmed-searcher/assets/58769230/1f7667c7-40cf-42b7-9d2d-05f124cbcce7)

1. 打开网页。
2. 在搜索表单中输入开始时间、截止时间、搜索结果数和搜索关键字。
3. 点击搜索按钮，页面将显示搜索结果。
4. 使用页面上的功能按钮对搜索结果进行操作。

### 注意事项

- 搜索表单的输入框有默认值，用户可以根据需要进行修改。
- 点击用户面板上的欢迎信息可以显示退出登录的下拉菜单。
- 搜索结果表格支持分页和排序功能，用户可以根据需要进行操作。
- 所有操作按钮均有相应的提示信息，用户可以根据提示进行操作。



### License
This project is released under [MIT License](https://github.com/sunbigfly/pubmed-searcher?tab=MIT-1-ov-file).


### 作者

by sunbigfly

请根据你的项目需求和实际情况调整上述步骤和代码。如有任何问题，请随时询问。
