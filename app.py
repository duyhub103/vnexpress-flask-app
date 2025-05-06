from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vnexpress2.db'
db = SQLAlchemy(app)

class ArticleModel(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    title = db.Column(db.String)
    description = db.Column(db.String)
    page_contents = db.Column(db.Text)
    category = db.Column(db.String)
    publish_date = db.Column(db.String)
    author = db.Column(db.String)

@app.route('/')
def home():
    return render_template('home.html')

# @app.route('/articles')
# def articles():
#     page = request.args.get('page', 1, type=int)
#     per_page = 20
#     pagination = ArticleModel.query.order_by(ArticleModel.id.desc()).paginate(page=page, per_page=per_page)
#     return render_template('articles.html', articles=pagination.items, pagination=pagination)
@app.route('/articles')
def articles():
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = ArticleModel.query
    if category:
        query = query.filter_by(category=category)
    pagination = query.order_by(ArticleModel.id.desc()).paginate(page=page, per_page=per_page)
    return render_template('articles.html', articles=pagination.items, pagination=pagination)


@app.route('/search')
def search():
    keyword = request.args.get('q')
    if keyword:
        articles = ArticleModel.query.filter(
            ArticleModel.title.ilike(f'%{keyword}%') |
            ArticleModel.description.ilike(f'%{keyword}%') |
            ArticleModel.page_contents.ilike(f'%{keyword}%')
        ).all()
    else:
        articles = []
    return render_template('search.html', articles=articles, keyword=keyword)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = ArticleModel.query.get_or_404(article_id)
    return render_template('article_detail.html', article=article)

if __name__ == '__main__':
    app.run(debug=True)
