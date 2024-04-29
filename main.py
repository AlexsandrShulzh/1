import os
import pymorphy2

from currency_converter import CurrencyConverter, RateNotFoundError
from flask import Flask, render_template, redirect
from flask_wtf.csrf import generate_csrf

from data import db_session
from data.comment import Comment
from data.form import MainForm, Commenting

app = Flask(__name__)
app.config['SECRET_KEY'] = 'myapp_secret_key'

converter = CurrencyConverter()
morph = pymorphy2.MorphAnalyzer()

# Обработчик страницы конвертации
@app.route("/", methods=['GET', 'POST'])
@app.route("/converting", methods=['GET', 'POST'])
def converting():
    # Инициализация форм
    currency_form = MainForm()
    commenting_form = Commenting()
    # Создание сессии базы данных
    db_sess = db_session.create_session()

    # Сбор данных с формы
    # Число - денежная величина
    value = currency_form.data_in.data
    # Исходная валюта
    curr_in = currency_form.select.data
    # В какую валюту конвертировать
    curr_out = currency_form.select2.data

    # Короткие символы валют
    curr_in_short = curr_in[:3]
    curr_out_short = curr_out[:3]
    
    # Первоначальное отсутствие данных
    if value is None:
        value = '0'
        curr_in = currency_form.select.default
        curr_out = currency_form.select2.default
    try:
        result = converter.convert(int(value), curr_in_short, curr_out_short)
        result = str(round(result, 2)) + ' ' + curr_out_short
    except ValueError:
        result = 'Ошибка ввода данных'
    except RateNotFoundError:
        result = 'Котировка валюты не найдена'

    # Конвертация единицы валюты
    try:
        result_ones = converter.convert(1, curr_in_short, curr_out_short)
        result_ones = str(round(result_ones, 2))
    except RateNotFoundError:
        result_ones = 'Котировка не найдена'

    return render_template(
        'converting.html',
        currency_form=currency_form,
        commenting_form=commenting_form,
        result=result,
        result_ones=f'1 {curr_in_short} равен {result_ones} {curr_out_short}',
        h_title=f'{curr_in[6:]} в {curr_out[6:]}',
        comments=reversed(db_sess.query(Comment).all()))


# Добавление комментария в БД
@app.route("/add_comment", methods=['GET', 'POST'])
def adding():
    currency_form = MainForm()
    commenting_form = Commenting()
    comment_db = Comment()
    db_sess = db_session.create_session()
    # Проверяем, есть ли пользователь с таким email в БД
    existing_user = db_sess.query(Comment).filter(Comment.email == commenting_form.email.data).first()
    
    if existing_user:
        # Если пользователь уже есть, обновляем его комментарий
        existing_user.text = commenting_form.comment.data
        db_sess.commit()
    else:
        # Проверяем, существует ли пользователь с таким же никнеймом
        existing_username = db_sess.query(Comment).filter(Comment.username == commenting_form.username.data).first()
        
        if existing_username:
                return render_template(
                'converting.html',
                currency_form=currency_form,
                commenting_form=commenting_form,
                nik = 'Имя пользователя уже занято. Пожалуйста, выберите другое имя.',
                comments=reversed(db_sess.query(Comment).all()))
                return redirect('/converting')
        
        # Если пользователя нет в БД , добавляем новый комментарий
        comment_db.text = commenting_form.comment.data
        comment_db.email = commenting_form.email.data
        comment_db.username = commenting_form.username.data
        db_sess.add(comment_db)
        db_sess.commit()
    
    # Для очистки БД раскомментровать эту строчку и заполнить бланк в комментариях
    #del_com()
    return redirect('/converting')


@app.route("/add_comment", methods=['GET', 'POST'])
def del_com():
    currency_form = MainForm()
    commenting_form = Commenting()
    comment_db = Comment()
    db_sess = db_session.create_session()
    db_sess = db_session.create_session()
    db_sess.query(Comment).delete()
    db_sess.commit()
    return redirect('/converting')


if __name__ == '__main__':
    db_session.global_init("db/comments.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)