import os
import shutil
import zipfile
import logging
import csv
from datetime import datetime
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

# 配置日志设置
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SOURCE_FOLDER = r"E:\qgis3.14.13\云梦\py"
DOWNLOAD_LOG_FILE = f"downloads_{datetime.now().strftime('%Y-%m-%d')}.csv"

# 创建 CSV 文件并写入表头
if not os.path.exists(DOWNLOAD_LOG_FILE):
    with open(DOWNLOAD_LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["文件名", "村民名"])  # 写入表头

def load_download_records():
    """从 CSV 文件加载下载记录"""
    records = []
    if os.path.exists(DOWNLOAD_LOG_FILE):
        with open(DOWNLOAD_LOG_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            records = list(reader)  # 将记录加载为列表
    return records


def copy_and_rename_files(source_folder, target_folder, new_name):
    file_names = [
        "资产点状图.cpg", "资产点状图.dbf", "资产点状图.prj", "资产点状图.qix",
        "资产点状图.shp", "资产点状图.shx", "资产面状图.cpg", "资产面状图.dbf",
        "资产面状图.prj", "资产面状图.shp", "资产面状图.shx", "资源面状图.cpg",
        "资源面状图.dbf", "资源面状图.prj", "资源面状图.qix", "资源面状图.shp",
        "资源面状图.shx"
    ]
    file_zy = [
        "0502 待界定建设用地",
        "0503 待界定未利用地",
        "0501 待界定农用地",
        "03 未利用地",
        "010102 未承包到户耕地",
        "010202 未承包到户园地",
        "010302 未承包到户林地",
        "010402 未承包到户草地",
        "0105 农田水利设施用地（沟渠）",
        "010602 未承包到户养殖水面（坑塘水面）",
        "019902 未承包到户其他农用地",
        "0201 工矿仓储用地",
        "0202 商服用地",
        "0204 公共管理与公共服务用地",
        "0205 交通运输和水利设施用地",
        "0299 其他建设用地",
        "04 “四荒”地",
        "0601 公益林",
        "0602 商品林"
    ]
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for old_name in file_names:
        old_file_path = os.path.join(source_folder, old_name)
        if os.path.exists(old_file_path):
            ext = old_name.split('.')[-1]

            if "资产点状图" in old_name:
                new_file_name = f"{new_name}_资产点状图.{ext}"
            elif "资产面状图" in old_name:
                new_file_name = f"{new_name}_资产面状图.{ext}"
            elif "资源面状图" in old_name:
                # 对于资源面状图，我们为每个file_zy条目创建一个新的文件夹
                for zy in file_zy:
                    zy_folder = os.path.join(target_folder, zy)
                    if not os.path.exists(zy_folder):
                        os.makedirs(zy_folder)  # 创建新文件夹
                    new_file_name = f"{new_name}_{zy}_资源面状图.{ext}"
                    new_file_path = os.path.join(zy_folder, new_file_name)

                    if os.path.exists(new_file_path):
                        logging.warning(f"文件 '{new_file_name}' 已存在，跳过复制")
                    else:
                        shutil.copy2(old_file_path, new_file_path)
                        logging.info(f"文件 '{old_name}' 已复制并重命名为 '{new_file_name}'")
                continue  # 跳过后续的资源面状图文件拷贝
            else:
                new_file_name = f"{new_name}_{old_name}"

            new_file_path = os.path.join(target_folder, new_file_name)

            if os.path.exists(new_file_path):
                logging.warning(f"文件 '{new_file_name}' 已存在，跳过复制")
            else:
                shutil.copy2(old_file_path, new_file_path)
                logging.info(f"文件 '{old_name}' 已复制并重命名为 '{new_file_name}'")
        else:
            logging.warning(f"文件 '{old_name}' 在源文件夹中不存在，跳过复制")


def create_zip(target_folder, zip_filename):
    zip_path = os.path.join(target_folder, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(target_folder):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, target_folder)
                zipf.write(file_path, arcname)
    return zip_path

@app.route('/', methods=['GET', 'POST'])
def index():
    download_records = load_download_records()  # 加载下载记录
    if request.method == 'POST':
        target_folder = os.path.join("temp_output", request.form['target_folder'])
        new_name = request.form['new_name']
        new_name2 = request.form['target_folder']
        copy_and_rename_files(SOURCE_FOLDER, target_folder, new_name)

        zip_filename = f"{new_name2}_files.zip"
        zip_path = create_zip(target_folder, zip_filename)

        # 保存下载记录到 CSV 文件
        with open(DOWNLOAD_LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([zip_filename, new_name])  # 写入文件名和村民名

        logging.info(f"已创建压缩包 '{zip_filename}'，准备下载")
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)

    return render_template('index.html', download_records=download_records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)