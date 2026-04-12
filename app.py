from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from movies_data import movies

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Brasil&-^'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
login_manager.login_message_category = 'error'


# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    movie_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание таблиц
with app.app_context():
    db.create_all()

MOVIES_PER_PAGE = 20


# Главная страница
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'rating')

    if search_query:
        filtered_movies = [
            movie for movie in movies
            if search_query.lower() in movie['title'].lower() or
               search_query.lower() in movie['genre'].lower()
        ]
    else:
        filtered_movies = movies.copy()

    if sort_by == 'rating':
        filtered_movies.sort(key=lambda x: x['rating'], reverse=True)
    elif sort_by == 'year':
        filtered_movies.sort(key=lambda x: x['year'], reverse=True)
    elif sort_by == 'title':
        filtered_movies.sort(key=lambda x: x['title'])

    total_movies = len(filtered_movies)
    total_pages = (total_movies + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE

    start_idx = (page - 1) * MOVIES_PER_PAGE
    end_idx = start_idx + MOVIES_PER_PAGE
    paginated_movies = filtered_movies[start_idx:end_idx]

    return render_template('index.html',
                           movies=paginated_movies,
                           search_query=search_query,
                           current_page=page,
                           total_pages=total_pages,
                           total_movies=total_movies,
                           sort_by=sort_by)


# Страница фильма с комментариями
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = next((m for m in movies if m['id'] == movie_id), None)
    if not movie:
        flash('Фильм не найден', 'error')
        return redirect(url_for('index'))

    comments = Comment.query.filter_by(movie_id=movie_id).order_by(Comment.created_at.desc()).all()

    # Подсчет средней оценки пользователей
    user_ratings = [c.rating for c in comments if c.rating]
    avg_user_rating = sum(user_ratings) / len(user_ratings) if user_ratings else None

    return render_template('movie_detail.html',
                           movie=movie,
                           comments=comments,
                           avg_user_rating=avg_user_rating,
                           total_comments=len(comments))


# Добавление комментария
@app.route('/movie/<int:movie_id>/comment', methods=['POST'])
@login_required
def add_comment(movie_id):
    movie = next((m for m in movies if m['id'] == movie_id), None)
    if not movie:
        flash('Фильм не найден', 'error')
        return redirect(url_for('index'))

    content = request.form.get('content', '').strip()
    rating_str = request.form.get('rating', '').strip()
    rating = None

    if rating_str:
        try:
            rating = int(rating_str)
            if rating < 1 or rating > 10:
                flash('Оценка должна быть от 1 до 10', 'error')
                return redirect(url_for('movie_detail', movie_id=movie_id))
        except ValueError:
            flash('Неверный формат оценки', 'error')
            return redirect(url_for('movie_detail', movie_id=movie_id))

    if not content:
        flash('Комментарий не может быть пустым', 'error')
        return redirect(url_for('movie_detail', movie_id=movie_id))

    comment = Comment(
        content=content,
        rating=rating,
        movie_id=movie_id,
        user_id=current_user.id
    )

    try:
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий успешно добавлен!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при добавлении комментария', 'error')
        print(f"Error: {e}")

    return redirect(url_for('movie_detail', movie_id=movie_id))


# Удаление комментария
@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id:
        flash('Вы не можете удалить чужой комментарий', 'error')
        return redirect(url_for('movie_detail', movie_id=comment.movie_id))

    movie_id = comment.movie_id

    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Комментарий удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении комментария', 'error')
        print(f"Error: {e}")

    return redirect(url_for('movie_detail', movie_id=movie_id))


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Валидация
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Имя пользователя должно быть не менее 3 символов', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован', 'error')
            return render_template('register.html')

            # Создание пользователя
        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации', 'error')
            print(f"Error: {e}")
            return render_template('register.html')

    return render_template('register.html')

    # Вход


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'true'

        if not username or not password:
            flash('Заполните все поля', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {user.username}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')

    # Выход


@app.route('/logout')


@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))


# Профиль пользователя
@app.route('/profile')
@login_required
def profile():
    user_comments = Comment.query.filter_by(user_id=current_user.id).order_by(Comment.created_at.desc()).all()

    # Получаем информацию о фильмах для комментариев
    comments_with_movies = []
    for comment in user_comments:
        movie = next((m for m in movies if m['id'] == comment.movie_id), None)
        if movie:
            comments_with_movies.append({
                'comment': comment,
                'movie': movie
            })

    return render_template('profile.html',
                           user=current_user,
                           comments_with_movies=comments_with_movies)


if __name__ == '__main__':
    app.run(debug=True)
