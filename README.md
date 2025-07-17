# MapReq

MapReq 是一个基于 Flask 和 Folium 的地图可视化项目，用于展示和筛选美国各州学校、学区和 PSAP 客户的地理分布，并支持数据的动态上传和更新。

## 功能特性

- 地图可视化：基于 Folium 展示学校、学区、PSAP 的地理位置。
- 多维筛选：支持按州/地区、站点类型（公立、私立、学区、PSAP）、客户类型（Crisisgo、E911、潜在客户等）筛选展示。
- 数据上传：支持通过前端上传 CSV/TXT 文件，批量更新客户数据。
- 交互式界面：前端可动态切换筛选条件，实时刷新地图。
- 数据库支持：后端使用 MySQL 存储和管理数据。

## 安装与运行

1. 克隆本项目：

    ```bash
    git clone https://github.com/yourusername/MapReq.git
    cd MapReq
    ```

2. 安装依赖：

    ```bash
    pip install flask folium mysql-connector-python
    ```

3. 配置数据库连接（如有需要请修改 `host`、`user`、`password`、`database`）。

4. 运行项目：

    ```bash
    python app.py
    ```

5. 在浏览器访问 [http://localhost:5000](http://localhost:5000)。

## 使用说明

- 主页会自动跳转到地图筛选页面。
- 右上角 `[Hide/Show] Filters` 可选择州/地区、站点类型和客户类型，点击 Confirm 后刷新地图。
- 左上角 `[Hide/Show] Update List` 可上传 CSV/TXT 文件，批量更新客户数据（请勿用 Excel 直接编辑 CSV）。
- 支持的上传格式：(内附示例文件)`[ncessch],[ppin_uuid],[psap_uuid],[leaid],[name]`。

## 注意事项

- 上传数据前请确保格式正确，避免因数据错误导致导入失败。
- 上传文件建议使用文本编辑器（如 VSCode、Notepad++）编辑，避免 Excel 格式兼容问题。
- 仅支持 `.csv` 和 `.txt` 文件上传。

## 依赖

- Flask
- Folium
- mysql-connector-python

## 许可证

MIT License
