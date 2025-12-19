from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Case, UserCase
from ai import ask_agent
import markdown
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ваш-секретный-ключ-сюда'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание БД
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html', user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с такой почтой уже существует')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Регистрация успешна!')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Вход выполнен успешно!')
            return redirect(url_for('home'))
        
        flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
@login_required
def generate_cases():
    user_input = request.form.get('mycasetext')
    
    if not user_input:
        flash('Введите описание для генерации кейсов')
        return redirect(url_for('home'))
    
    # Генерация кейсов через ИИ
    ai_response = ask_agent(user_input)
    
    cases = []
    if "cases" in ai_response and ai_response["cases"]:
        for case_data in ai_response["cases"]:
            # Конвертируем описание в HTML
            full_desc_html = markdown.markdown(
                case_data.get('full_description', ''), 
                extensions=["fenced_code"]
            )
            
            case = Case(
                title=case_data.get('title', 'Без названия'),
                level=case_data.get('level', 'junior'),
                duration=case_data.get('duration', '2 недели'),
                short_description=case_data.get('short_description', ''),
                full_description=full_desc_html,
                tags=', '.join(case_data.get('tags', [])) if isinstance(case_data.get('tags'), list) else case_data.get('tags', '')
            )
            
            db.session.add(case)
            db.session.flush()  # Получаем ID кейса
            
            # Проверяем, сохранен ли уже кейс пользователем
            is_saved = UserCase.query.filter_by(
                user_id=current_user.id, 
                case_id=case.id
            ).first() is not None
            
            cases.append({
                'id': case.id,
                'title': case.title,
                'level': case.level,
                'duration': case.duration,
                'short_description': case.short_description,
                'full_description': case.full_description,
                'is_saved': is_saved
            })
        
        db.session.commit()
    
    return jsonify({'cases': cases})

@app.route('/save_case/<int:case_id>', methods=['POST'])
@login_required
def save_case(case_id):
    # Проверяем, не сохранен ли уже кейс
    existing = UserCase.query.filter_by(
        user_id=current_user.id, 
        case_id=case_id
    ).first()
    
    if existing:
        # Удаляем из сохраненных
        db.session.delete(existing)
        db.session.commit()
        return jsonify({
            'success': True, 
            'action': 'removed', 
            'message': 'Кейс удален из "Мои кейсы"'
        })
    else:
        # Добавляем в сохраненные
        user_case = UserCase(user_id=current_user.id, case_id=case_id)
        db.session.add(user_case)
        db.session.commit()
        return jsonify({
            'success': True, 
            'action': 'added', 
            'message': 'Кейс добавлен в "Мои кейсы"'
        })

@app.route('/my_cases')
@login_required
def my_cases():
    # Получаем сохраненные кейсы пользователя
    saved_cases = UserCase.query.filter_by(user_id=current_user.id)\
        .order_by(UserCase.saved_at.desc())\
        .all()
    
    cases_data = []
    for user_case in saved_cases:
        case = user_case.case
        cases_data.append({
            'id': case.id,
            'title': case.title,
            'level': case.level,
            'duration': case.duration,
            'short_description': case.short_description,
            'full_description': case.full_description,
            'saved_at': user_case.saved_at.strftime('%d.%m.%Y'),
            'is_completed': user_case.is_completed
        })
    
    return render_template('my_cases.html', 
                         cases=cases_data, 
                         user=current_user)

@app.route('/complete_case/<int:case_id>', methods=['POST'])
@login_required
def complete_case(case_id):
    user_case = UserCase.query.filter_by(
        user_id=current_user.id, 
        case_id=case_id
    ).first()
    
    if user_case:
        user_case.is_completed = not user_case.is_completed
        user_case.completed_at = datetime.utcnow() if user_case.is_completed else None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_completed': user_case.is_completed
        })
    
    return jsonify({'success': False}), 404

if __name__ == '__main__':

    app.run(debug=True)
else:
    # Для запуска на Vercel (как серверless-функция)
    application = app
