from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from markupsafe import Markup
from xhtml2pdf import pisa
import re
import io

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

@app.route('/articles')
def articles():
    category = request.args.get('category')  # Lấy danh mục từ query string
    page = request.args.get('page', 1, type=int)
    per_page = 20
    sort_by = request.args.get('sort_by', 'newest')  # Mặc định sắp xếp theo mới nhất

    total_count = ArticleModel.query.count()
    # Lấy tất cả danh mục từ cơ sở dữ liệu
    category_counts = db.session.query(
    ArticleModel.category,
    func.count(ArticleModel.id)
    ).group_by(ArticleModel.category).all()

    query = ArticleModel.query

    # Lọc theo thể loại (danh mục)
    if category:
        query = query.filter_by(category=category)

    # Sắp xếp theo thời gian
    if sort_by == 'oldest':  # Sắp xếp theo cũ nhất
        query = query.order_by(ArticleModel.publish_date.asc())  # Sắp xếp theo ngày tăng dần (cũ nhất)
    else:  # Mặc định sắp xếp theo mới nhất
        query = query.order_by(ArticleModel.publish_date.desc())  # Sắp xếp theo ngày giảm dần (mới nhất)

    pagination = query.paginate(page=page, per_page=per_page)
    
    # Tính số thứ tự
    start_index = (pagination.page - 1) * pagination.per_page
    
    return render_template(
    'articles.html',
    articles=pagination.items,
    pagination=pagination,
    start_index=start_index,
    sort_by=sort_by,
    category=category,
    categories=category_counts,
    total_count=total_count
)




from datetime import datetime, timedelta

# @app.route('/articles')
# def articles():
#     category = request.args.get('category')  # Lấy danh mục từ query string
#     page = request.args.get('page', 1, type=int)
#     per_page = 20
#     sort_by = request.args.get('sort_by', 'newest')  # Mặc định sắp xếp theo mới nhất
 
#     query = ArticleModel.query

#     # Lọc theo thể loại (danh mục)
#     if category:
#         query = query.filter_by(category=category)
    
#     # Sắp xếp theo thời gian
#     if sort_by == 'oldest':  # Sắp xếp theo cũ nhất
#         query = query.order_by(ArticleModel.publish_date.asc())  # Sắp xếp theo ngày tăng dần (cũ nhất)
#     else:  # Mặc định sắp xếp theo mới nhất
#         query = query.order_by(ArticleModel.publish_date.desc())  # Sắp xếp theo ngày giảm dần (mới nhất)

#     pagination = query.paginate(page=page, per_page=per_page)
    
#     # Tính số thứ tự
#     start_index = (pagination.page - 1) * pagination.per_page
    
#     return render_template('articles.html', articles=pagination.items, pagination=pagination, start_index=start_index, sort_by=sort_by, category=category)



@app.route('/search')
def search():
    keyword = request.args.get('q')
    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = None

    if keyword:
        query = ArticleModel.query.filter(
            ArticleModel.title.ilike(f'%{keyword}%') |
            ArticleModel.description.ilike(f'%{keyword}%') |
            ArticleModel.page_contents.ilike(f'%{keyword}%')
        )
        # Sắp xếp theo ngày
        if sort_by == 'oldest':
            query = query.order_by(ArticleModel.publish_date.asc())
        else:
            query = query.order_by(ArticleModel.publish_date.desc())

        pagination = query.paginate(page=page, per_page=per_page)
        articles = pagination.items
    else:
        articles = []

    start_index = (page - 1) * per_page
    return render_template('search.html', articles=articles, keyword=keyword, sort_by=sort_by, pagination=pagination, start_index=start_index)


@app.template_filter('highlight')
def highlight(text, keyword):
    if not keyword or not text:
        return text
    # Dùng regex để tìm từ khóa bất kể hoa/thường
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<span style="background-color: yellow;">{m.group(0)}</span>', text)
    return Markup(highlighted)


@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = ArticleModel.query.get_or_404(article_id)

    # Lấy 4 bài viết liên quan cùng danh mục, loại trừ bài hiện tại
    related_articles = ArticleModel.query.filter(
        ArticleModel.category == article.category,
        ArticleModel.id != article.id
    ).order_by(ArticleModel.publish_date.desc()).limit(4).all()

    return render_template('article_detail.html', article=article, related_articles=related_articles)


# Route xuất danh sách bài báo thành PDF
@app.route('/articles/pdf')
def export_articles_pdf():
    articles = ArticleModel.query.order_by(ArticleModel.id.desc()).all()
    html = render_template("articles_pdf.html", articles=articles)
    
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    
    if pisa_status.err:
        return "Lỗi khi tạo PDF"
    
    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=danh_sach_bai_bao.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
