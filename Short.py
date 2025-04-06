import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import hashlib
import random
import string

short_url_flask_app = Flask(__name__)
# 使用环境变量管理密钥
short_url_flask_app.secret_key = os.environ.get('SECRET_KEY', 'short_url')

# 使用SQLAlchemy管理数据库连接
short_url_flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
short_url_flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(short_url_flask_app)

# 定义模型类
class Urls(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    short_url = db.Column(db.Text, unique=True, nullable=False)
    long_url = db.Column(db.Text, nullable=False)

with short_url_flask_app.app_context():
    db.create_all()

def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def save_url(long_url, short_url):
    new_link = Urls(long_url=long_url, short_url=short_url)
    db.session.add(new_link)
    db.session.commit()

def check_if_short_url_exists(short_url):
    return Urls.query.filter_by(short_url=short_url).first() is not None

def create_short_url(long_url, custom_suffix=None):
    # 合并长链接与自定义后缀，确保URL格式正确
    if custom_suffix:
        combined_url = long_url.rstrip('/') + '/' + custom_suffix.lstrip('/')
    else:
        combined_url = long_url

    # 使用哈希生成短链接，并检查该短链接是否已存在
    short_url = hashlib.md5(combined_url.encode()).hexdigest()[:6]

    # 确保短链接唯一
    while check_if_short_url_exists(short_url):
        short_url = generate_random_string(6)  # 如果短链接已存在，则重新生成

    return short_url, combined_url

# 路由：主页，显示输入框
@short_url_flask_app.route("/short/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form["long_url"]
        custom_suffix = request.form["custom_suffix"]

        if not long_url:
            return render_template("index.html", error="请输入一个有效的长链接！")

        # 检查长链接是否已存在
        existing_link = Urls.query.filter_by(long_url=long_url).first()
        if existing_link:
            # 如果长链接已存在，直接返回现有的短链接
            short_url = existing_link.short_url
        else:
            # 创建短链接和合并后的长链接
            short_url, combined_url = create_short_url(long_url, custom_suffix)
            # 将链接保存到数据库
            save_url(combined_url, short_url)

        return render_template("index.html", short_url=short_url)

    return render_template("index.html")

# 路由：处理短链接访问
@short_url_flask_app.route("/short/<short_url>")
def redirect_to_long_url(short_url):
    link = Urls.query.filter_by(short_url=short_url).first()
    if link:
        # 重定向到长链接
        return redirect(link.long_url)
    else:
        # 如果找不到短链接，返回 404
        return "Short URL not found!", 404

if __name__ == '__main__':
    # 启动 Flask 应用
    short_url_flask_app.run(debug=True, host='127.0.0.1', port=5000)
