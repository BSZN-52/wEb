import os

# Создаем папки
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

print("✓ Папки созданы")

# Создаем index.html
index_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Каталог фильмов</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎬 Каталог фильмов</h1>
            <p class="subtitle">Коллекция из {{ total_movies }} лучших фильмов всех времён</p>
            <nav class="header-nav">
                {% if current_user.is_authenticated %}
                    <span>Привет, {{ current_user.username }}!</span>
                    <a href="{{ url_for('profile') }}">Профиль</a>
                    <a href="{{ url_for('logout') }}">Выход</a>
                {% else %}
                    <a href="{{ url_for('login') }}">Вход</a>
                    <a href="{{ url_for('register') }}">Регистрация</a>
                {% endif %}
            </nav>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="search-section">
            <form method="GET" action="/" class="search-form">
                <input type="text" name="search" placeholder="Поиск..." value="{{ search_query }}" class="search-input">
                <button type="submit" class="search-btn">🔍 Найти</button>
            </form>

            <div class="filter-section">
                <label>Сортировка:</label>
                <a href="/?sort=rating{% if search_query %}&search={{ search_query }}{% endif %}" 
                   class="filter-btn {% if sort_by == 'rating' %}active{% endif %}">⭐ По рейтингу</a>
                <a href="/?sort=year{% if search_query %}&search={{ search_query }}{% endif %}" 
                   class="filter-btn {% if sort_by == 'year' %}active{% endif %}">📅 По году</a>
                <a href="/?sort=title{% if search_query %}&search={{ search_query }}{% endif %}" 
                   class="filter-btn {% if sort_by == 'title' %}active{% endif %}">🔤 По названию</a>
            </div>
        </div>

        <div class="movies-grid">
            {% for movie in movies %}
            <div class="movie-card">
                <div class="movie-header">
                    <h2 class="movie-title">{{ movie.title }}</h2>
                    <span class="rating excellent">⭐ {{ movie.rating }}</span>
                </div>
                <div class="movie-info">
                    <p><strong>Год:</strong> {{ movie.year }}</p>
                    <p><strong>Жанр:</strong> <span class="genre-tag">{{ movie.genre }}</span></p>
                </div>
                <div class="movie-actions">
                    <a href="{{ url_for('movie_detail', movie_id=movie.id) }}" class="btn-view">Подробнее</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>'''

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
print("✓ Создан index.html")

# Создаем movie_detail.html
movie_detail_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ movie.title }} - Каталог фильмов</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <header>
<h1>🎬 {{ movie.title }}</h1>
            <nav class="header-nav">
                <a href="{{ url_for('index') }}">← Назад</a>
                {% if current_user.is_authenticated %}
                    <span>{{ current_user.username }}</span>
                    <a href="{{ url_for('profile') }}">Профиль</a>
                    <a href="{{ url_for('logout') }}">Выход</a>
                {% else %}
                    <a href="{{ url_for('login') }}">Вход</a>
                    <a href="{{ url_for('register') }}">Регистрация</a>
                {% endif %}
            </nav>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="movie-detail">
            <div class="movie-info-detailed">
                <div class="info-row">
                    <span class="label">Рейтинг IMDB:</span>
                    <span class="rating-large excellent">⭐ {{ movie.rating }}</span>
                </div>
                {% if avg_user_rating %}
                <div class="info-row">
                    <span class="label">Оценка пользователей:</span>
                    <span class="rating-large good">👥 {{ "%.1f"|format(avg_user_rating) }}/10</span>
                </div>
                {% endif %}
                <div class="info-row">
                    <span class="label">Год:</span>
                    <span class="value">{{ movie.year }}</span>
                </div>
                <div class="info-row">
                    <span class="label">Жанр:</span>
                    <span class="genre-tag">{{ movie.genre }}</span>
                </div>
                <div class="info-row">
                    <span class="label">Комментариев:</span>
                    <span class="value">{{ total_comments }}</span>
                </div>
            </div>

            <div class="comments-section">
                <h2>💬 Комментарии ({{ total_comments }})</h2>

                {% if current_user.is_authenticated %}
                <div class="comment-form">
                    <h3>Оставить комментарий</h3>
                    <form method="POST" action="{{ url_for('add_comment', movie_id=movie.id) }}">
                        <div class="form-group">
                            <label for="rating">Ваша оценка:</label>
                            <select name="rating" id="rating" class="rating-select">
                                <option value="">Без оценки</option>
                                <option value="10">10 - Шедевр</option>
                                <option value="9">9 - Отлично</option>
                                <option value="8">8 - Очень хорошо</option>
                                <option value="7">7 - Хорошо</option>
                                <option value="6">6 - Нормально</option>
                                <option value="5">5 - Посредственно</option>
                                <option value="4">4 - Плохо</option>
                                <option value="3">3 - Очень плохо</option>
                                <option value="2">2 - Ужасно</option>
                                <option value="1">1 - Кошмар</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="content">Комментарий:</label>
                            <textarea name="content" id="content" rows="4" required></textarea>
                        </div>
                        <button type="submit" class="btn-primary">Отправить</button>
</form>
                </div>
                {% else %}
                <div class="login-prompt">
                    <p>🔒 <a href="{{ url_for('login') }}">Войдите</a> или <a href="{{ url_for('register') }}">зарегистрируйтесь</a></p>
                </div>
                {% endif %}

                <div class="comments-list">
                    {% if comments %}
                        {% for comment in comments %}
                        <div class="comment">
                            <div class="comment-header">
                                <div class="comment-author">
                                    <strong>👤 {{ comment.author.username }}</strong>
                                    {% if comment.rating %}
                                        <span class="comment-rating">⭐ {{ comment.rating }}/10</span>
                                    {% endif %}
                                </div>
                                <div class="comment-meta">
                                    <span class="comment-date">{{ comment.created_at.strftime('%d.%m.%Y %H:%M') }}</span>
                                    {% if current_user.is_authenticated and comment.user_id == current_user.id %}
                                    <form method="POST" action="{{ url_for('delete_comment', comment_id=comment.id) }}" style="display:inline;">
                                        <button type="submit" class="btn-delete">🗑️</button>
                                    </form>
                                    {% endif %}
                                </div>
                            </div>
                            <div class="comment-content">{{ comment.content }}</div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="no-comments">
                            <p>Пока нет комментариев. Будьте первым!</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

with open('templates/movie_detail.html', 'w', encoding='utf-8') as f:
    f.write(movie_detail_html)
print("✓ Создан movie_detail.html")

# Создаем login.html
login_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="auth-container">
        <div class="auth-box">
            <h1>🎬 Вход</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label>Имя пользователя</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Пароль</label>
                    <input type="password" name="password" required>
                </div>
                <div class="form-group checkbox-group">
                    <label><input type="checkbox" name="remember" value="true"> Запомнить</label>
                </div>
                <button type="submit" class="btn-primary">Войти</button>
            </form>
            <div class="auth-links">
                <p><a href="{{ url_for('register') }}">Регистрация</a></p>
                <p><a href="{{ url_for('index') }}">← На главную</a></p>
            </div>
        </div>
    </div>
</body>
</html>'''

with open('templates/login.html', 'w', encoding='utf-8') as f:
    f.write(login_html)
print("✓ Создан login.html")
# Создаем register.html
register_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Регистрация</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="auth-container">
        <div class="auth-box">
            <h1>🎬 Регистрация</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label>Имя пользователя</label>
                    <input type="text" name="username" required minlength="3">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Пароль</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Подтвердите пароль</label>
                    <input type="password" name="confirm_password" required>
                </div>
                <button type="submit" class="btn-primary">Зарегистрироваться</button>
            </form>
            <div class="auth-links">
                <p><a href="{{ url_for('login') }}">Уже есть аккаунт?</a></p>
                <p><a href="{{ url_for('index') }}">← На главную</a></p>
            </div>
        </div>
    </div>
</body>
</html>'''

with open('templates/register.html', 'w', encoding='utf-8') as f:
    f.write(register_html)
print("✓ Создан register.html")

# Создаем profile.html
profile_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Профиль</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>👤 Профиль</h1>
            <nav class="header-nav">
                <a href="{{ url_for('index') }}">← На главную</a>
                <a href="{{ url_for('logout') }}">Выход</a>
            </nav>
        </header>
        <div class="profile-container">
            <div class="profile-info">
                <h2>{{ user.username }}</h2>
                <p><strong>Email:</strong> {{ user.email }}</p>
                <p><strong>Регистрация:</strong> {{ user.created_at.strftime('%d.%m.%Y') }}</p>
                <p><strong>Комментариев:</strong> {{ comments_with_movies|length }}</p>
            </div>
            <div class="user-comments-section">
                <h2>Ваши комментарии</h2>
                {% if comments_with_movies %}
                    {% for item in comments_with_movies %}
                    <div class="user-comment-card">
                        <div class="comment-movie-title">
                            <a href="{{ url_for('movie_detail', movie_id=item.movie.id) }}">
                                🎬 {{ item.movie.title }} ({{ item.movie.year }})
                            </a>
                            {% if item.comment.rating %}
                                <span class="comment-rating">⭐ {{ item.comment.rating }}/10</span>
                            {% endif %}
                        </div>
                        <div class="comment-text">{{ item.comment.content }}</div>
                        <div class="comment-footer">
                            <span class="comment-date">{{ item.comment.created_at.strftime('%d.%m.%Y') }}</span>
<form method="POST" action="{{ url_for('delete_comment', comment_id=item.comment.id) }}" style="display:inline;">
                                <button type="submit" class="btn-delete-small">Удалить</button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>У вас пока нет комментариев</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>'''

with open('templates/profile.html', 'w', encoding='utf-8') as f:
    f.write(profile_html)
print("✓ Создан profile.html")

print("\n✅ Все шаблоны успешно созданы!")
print("\nТеперь запустите: python app.py")