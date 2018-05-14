# -*- coding:utf8 -*-

from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import sys
reload(sys)
sys.setdefaultencoding("utf8")


app = Flask(__name__)

# 数据库配置：数据库地址/关闭自动跟踪修改
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1/flask_books'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'itheima'

# 创建数据库对象
db = SQLAlchemy(app)

'''
1.配置数据库
    a.导入SQLAlchemy拓展
    b.创建db对象，并配置参数
    c.终端创建数据库
2.添加书和作者的模型
    a.模型继承db.Model
    b.__tablename__表名
    c.db.Column:字段
    d.db.relationship:关系引用
3.添加数据
4.使用模板显示数据库查询的数据
    a.查询所有的作者信息，让信息传递给模板
    b.模板中按照格式，依次for循环作者和书籍即可（作者获取书籍，用的是引用关系）
5.使用wtf显示表单
    a.自定义表单类
    b.模板中显示
    c.secret_key / 编码 /  csrf_token
6.实现相关的增删逻辑
    a.增加数据
    b.删除书籍 --> 网页中删除 --> 点击需要发送书籍的ID给删除书籍的路由 --> 路由需要接受参数
    url_for的使用 / for else的使用
    c.删除作者
'''


# 定义书和作者模型
# 作者模型
class Author(db.Model):
    # 表名
    __tablename__ = 'authors'

    # 字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)

    # 关系引用
    # books是给自己（Author模型）用的，author是给Book模型用的
    books = db.relationship('Book', backref='author')

    def __repr__(self):
        return 'Author:%s' % self.name


# 书籍模型
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))

    def __repr__(self):
        return 'Book:%s %s' % (self.name, self.author_id)


# 自定义表单类
class AuthorForm(FlaskForm):
    author = StringField('author',validators=[DataRequired()])
    book = StringField('book', validators=[DataRequired()])
    submit = SubmitField('submit')


@app.route('/delete_author/<author_id>')
def delete_author(author_id):
    # 查询数据库，如果有作者，则删除其名下的书籍和作者。如果没有则提示错误
    author = Author.query.get(author_id)
    if author:
        try:
            Book.query.filter_by(author_id=author_id).delete()
            db.session.delete(author)
            db.session.commit()
        except Exception as e:
            print e
            flash('Delete author failed.')
            db.session.rollback()
    else:
        flash('The author not exists.')
    return redirect(url_for('index'))


@app.route('/delete_book/<book_id>')
def delete_book(book_id):
    # 查询数据库，是否该ID的书，如果有就删除，没有就提示错误
    book = Book.query.get(book_id)
    if book:
        try:
            db.session.delete(book)
            db.session.commit()
        except Exception as e:
            flash('Delete book failed.')
            db.session.rollback()
    else:
        flash('Can not find the book.')

    # 如何返回当前网址 --> 重定向
    # redirect:重定向，需要传入网络或者路由地址
    # url_for:需要传入视图函数名，返回该视图函数对应的路由地址
    return redirect(url_for('index'))


@app.route('/', methods=["GET","POST"])
def index():
    # 创建自定义的表单类
    author_form = AuthorForm()

    '''
    验证逻辑：
    1.调用wtf的函数实现验证
    2.验证获取数据
    3.判断作者是否存在
    4.如果作者存在，判断书籍是否存在，没有重复书籍就添加数据，如果重复就提示错误
    5.如果作者不存在，添加作者和书籍
    6.验证不通过就提示错误
    '''
    if author_form.validate_on_submit():
        # 2.验证获取数据
        author_name = author_form.author.data
        book_name = author_form.book.data

        # 3.判断作者是否存在
        author = Author.query.filter_by(name=author_name).first()

        # 4.如果作者存在，判断书籍是否存在，没有重复书籍就添加数据，如果重复就提示错误
        if author:
            book = Book.query.filter_by(name=book_name).first()
            if book:
                flash('The book already exists.')
            else:
                try:
                    new_book = Book(name=book_name,author_id=author.id)
                    db.session.add(new_book)
                    db.session.commit()
                except Exception as e:
                    print e
                    flash('Insert book failed.')
                    db.session.rollback()

        # 5.如果作者不存在，添加作者和书籍
        else:
            try:
                new_author = Author(name=author_name)
                db.session.add(new_author)
                db.session.commit()

                new_book = Book(name=book_name, author_id=new_author.id)
                db.session.add(new_book)
                db.session.commit()
            except Exception,e:
                print e
                flash('Insert author and book failed.')
                db.session.rollback()

    else:
        if request.method == 'POST':
            flash('information not completed')

    # 查询所有的作者信息，让信息传递给模板
    authors = Author.query.all()
    return render_template('books.html', authors=authors, form=author_form)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    # 生成数据
    au1 = Author(name='老王')
    au2 = Author(name='老惠')
    au3 = Author(name='老刘')
    # 把数据提交给用户回话
    db.session.add_all([au1, au2, au3])
    # 提交会话
    db.session.commit()

    bk1 = Book(name='老王回忆录', author_id=au1.id)
    bk2 = Book(name='我读书少，你别骗我', author_id=au1.id)
    bk3 = Book(name='如何才能让自己更骚', author_id=au2.id)
    bk4 = Book(name='怎样征服美丽少女', author_id=au3.id)
    bk5 = Book(name='如何征服英俊少男', author_id=au3.id)
    db.session.add_all([bk1, bk2, bk3, bk4, bk5])
    db.session.commit()

    app.run(debug=True)

