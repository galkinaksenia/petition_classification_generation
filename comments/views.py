import matplotlib
matplotlib.use('Agg')  # Использование режима Agg для генерации изображений без GUI
from django.shortcuts import render, redirect, get_object_or_404
from .models import Comment, ErrorLog
from .forms import CommentForm, CommentFilter
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import vk_api
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import time
import requests
import random
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI
from langchain_google_genai import HarmBlockThreshold, HarmCategory
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate
from langchain_core.output_parsers import NumberedListOutputParser
import pickle
import matplotlib.pyplot as plt
import numpy as np
from .models import Comment
from io import BytesIO
import base64
from django.db.models import Count
nltk.download('stopwords')

with open('comments/my_model.pickle', 'rb') as model_file:
    loaded_model = pickle.load(model_file)

with open('comments/vectorizer.pickle', 'rb') as vec_file:
    vectorizer = pickle.load(vec_file)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Если пользователь аутентифицирован, перенаправляем на страницу ввода кода
            login(request, user)
            return redirect('comment_list')
        else:
            ErrorLog.objects.create(message='Неуспешная попытка входа', status='Необработанная')
            messages.error(request, "Неправильное имя пользователя или пароль.")
    return render(request, 'login.html')
@login_required
def comment_list(request):
    print("Представление comment_list было вызвано.")

    comments = Comment.objects.all()
    sort_by = request.GET.get('sort', 'id')  # По умолчанию сортируем по ID
    if sort_by in ['sender_name', 'created_at', 'deadline', 'status', 'category', 'responsible']:
        comments = comments.order_by(sort_by)  # Сортируем заявки по указанному полю
    comment_filter = CommentFilter(request.GET, queryset=comments)
    comments = comment_filter.qs

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('comment_list')  # Перенаправление после успешной отправки
    else:
        form = CommentForm()

        # Проверка, была ли нажата кнопка для получения комментариев
    if request.method == 'GET':
        print(f"Запрос GET: {request.GET}")  # Печать параметров запроса
        if 'fetch_comments' in request.GET:
            print("Кнопка для получения комментариев была нажата.")
            owner_id = '-211041018'  # Замените на ID владельца поста
            start_date_str = request.GET.get('start_date')  # Получаем дату из формы
            print(f"Дата, введенная пользователем: {start_date_str}")  # Отладочное сообщение
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')  # Преобразуем строку в datetime
            print(f"Преобразованная дата: {start_date}")  # Отладочное сообщение
            fetch_vk_comments(owner_id, start_date)
            return redirect('comment_list')  # Перенаправление для обновления списка комментариев
        # Обработка удаления комментария
    if request.method == 'POST' and 'delete_comment' in request.POST:
        comment_id = request.POST.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)
        comment.delete()  # Удаление комментария
        return redirect('comment_list')

    return render(request, 'comment_list.html', {'comments': comments, 'form': form, 'filter': comment_filter})

@login_required
def add_comment(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                sender_name=form.cleaned_data['sender_name'],
                content=form.cleaned_data['content'],
                answer=generate_answer(form.cleaned_data['content']),
                created_at=datetime.now(),
                status=form.cleaned_data['status'],
                category=classify_comment(form.cleaned_data['content']),
                responsible=form.cleaned_data['responsible'],
                deadline=form.cleaned_data['deadline']
            )
            return redirect('comment_list')  # Перенаправление после успешного добавления
    else:
        form = CommentForm()

    return render(request, 'add_comment.html', {'form': form})

@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('comment_list')  # Перенаправление после успешного редактирования
    else:
        form = CommentForm(instance=comment)

    return render(request, 'edit_comment.html', {'form': form, 'comment': comment})

def fetch_vk_comments(owner_id, start_date):
    all_posts = []
    offset = 0

    while True:
        response = requests.get(
            'https://api.vk.com/method/wall.get',
            params={
                'owner_id': '-211041018',
                'count': 10,
                'offset': offset,
                'access_token': 'cf09d637cf09d637cf09d6377bcc21978accf09cf09d637a89e881907ac9fa80ffff3b0',
                'v': '5.131'  # Используйте последнюю версию API
            }
        )

        data = response.json()
        all_posts.extend(data.get('response', {}).get('items', []))
        offset += 10
        oldest_comment_date = datetime.fromtimestamp(all_posts[-1]['date'])
        if oldest_comment_date <= start_date:
            break
        time.sleep(1)  # Обязательно добавьте задержку, чтобы не превышать лимиты API
    try:
        vk_session = vk_api.VkApi(token='cf09d637cf09d637cf09d6377bcc21978accf09cf09d637a89e881907ac9fa80ffff3b0')
        vk = vk_session.get_api()
        for post in all_posts:
            post_id = post['id']
            # Получаем комментарии к посту
            comments = vk.wall.getComments(owner_id='-211041018', post_id=post_id, count=10)
            for comment in comments['items']:
                if vk.users.get(user_ids=comment.get('from_id')):
                    user_get = vk.users.get(user_ids=comment.get('from_id'))[0]
                    sender_name = user_get['first_name'] + user_get['last_name']
                    content = comment.get('text')
                    created_at = datetime.fromtimestamp(comment.get('date'))
                    if created_at <= start_date:
                        continue
                    if not Comment.objects.filter(sender_name=sender_name, content=content).exists():
                        Comment.objects.create(
                            sender_name=sender_name,
                            content=content,
                            answer=generate_answer(content + ' опубликовано в ' + str(created_at)),
                            created_at=created_at,
                            status='Новое',
                            category=classify_comment(content),
                            responsible='Иванов',
                            deadline='2025-06-06'
                        )
    except Exception as e:
        ErrorLog.objects.create(message=str(e), status='Неисправность')

def classify_comment(comment):
    comment_vec = vectorizer.transform([comment])
    prediction = loaded_model.predict(comment_vec)
    return prediction[0]

def generate_answer_model(examples, petition):
    text_prompt = '''
    Задание: Тебе дан текст обращения гражданина в Администрацию Ленинского района города Нижнего Новгорода. Тебе необходимо составить ответ на него, используя структуру примера ответа.

    Обязательно: Не дополняй ответ лишними данными. В ответе выдавай только текст ответа на обращение.

    Обращение, на которое нужно дать ответ:
    {petition}

    Примеры структуры ответов:
    {examples}

    {format_instr}
    '''
    exmpl_prompt = '''
    Текст: {text}
    '''
    safety_settings = {HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                       HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                       HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                       HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE}
    model = GoogleGenerativeAI(model='gemini-2.0-flash-exp',
                               api_key='AIzaSyCo48Nu9dcYIkzvDMQYE1sW8TbTtpXcj_o',
                               temperature=0.9,
                               safety_settings=safety_settings,
                               frequencyPenalty=1.2,
                               presencePenalty=1.4
                               )

    parser = NumberedListOutputParser()

    random_examples = random.sample(examples, min(len(examples), 5))

    example_prompt = PromptTemplate.from_template(exmpl_prompt)
    examples_prompt = FewShotPromptTemplate(
        examples=random_examples,
        example_prompt=example_prompt,
        suffix='')

    prompt = PromptTemplate(template=text_prompt,
                            partial_variables={"petition": petition,
                                               "examples": examples_prompt.invoke({'input': ''}).to_string(),
                                               "format_instr": parser.get_format_instructions()})

    chain = prompt | model | parser

    return chain.invoke({'input': ''})

def generate_answer(petition):
    data = pd.read_excel('comments/Lobachevskiy.xlsx', index_col=0)
    examples_l = []
    for i, row in data.iterrows():
        examples_l.append(f'{row["Ответ на обращение"]}')
    examples_l = [{'text': i} for i in examples_l]
    load_dotenv()
    answer = generate_answer_model(examples_l, petition)

    return ' '.join(answer)

def comment_statistics(request):
    total_comments = Comment.objects.count()

    # Подсчет заявок по статусу
    category_counts = Comment.objects.values('category').annotate(category_count=Count('id'))

    # Создаем графики
    fig, ax = plt.subplots(figsize=(15, 10))

    # График по статусам заявок
    categories = [cat['category'] for cat in category_counts]

    comment_counts = [cat['category_count'] for cat in category_counts]

    ax.bar(categories, comment_counts, color='blue')
    ax.set_title('Количество обращений по категориям')
    ax.set_xlabel('Категории')
    ax.set_ylabel('Количество обращений')
    plt.xticks(rotation=30)

    # Генерация круговой диаграммы
    #fig, ax = plt.subplots(figsize=(10, 6))
    #ax.pie(comment_counts, labels=categories, autopct='%1.1f%%', startangle=90,
    #       colors=plt.cm.Paired(np.linspace(0, 1, len(categories))))
    #ax.axis('equal')  # Равные масштабы для корректного отображения круга
    #plt.title('Процент комментариев по категориям')

    # Сохранение графика в объект BytesIO и преобразование в base64
    buffer = BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buffer)
    img = buffer.getvalue()
    img_b64 = base64.b64encode(img).decode('utf-8')  # Кодируем в base64 строку

    context = {
        'total_comments': total_comments,
        'category_counts': category_counts,
        'status_chart': img_b64,  # передаем изображение диаграммы в контекст
    }
    return render(request, 'comment_statistics.html', context)



'''
@login_required
def fetch_vk_comments(request):
    if request.method == "POST":
        group_id = request.POST.get('group_id')  # ID сообщества
        post_id = request.POST.get('post_id')    # ID поста, к которому получаем комментарии

        # Инициализация сессии ВК
        vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
        vk = vk_session.get_api()

        try:
            # Получение комментариев
            comments = vk.wall.getComments(owner_id=-int(group_id), post_id=post_id)

            # Обработка комментариев и сохранение в базу данных
            for comment in comments['items']:
                Comment.objects.get_or_create(
                    vk_comment_id=comment['id'],
                    content=comment['text'],
                    user=request.user,
                    status='pending',
                    category='default'  # Можно добавить логику для классификации
                )

            return JsonResponse({'status': 'success', 'message': 'Комментарии успешно загружены.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Неверный метод запроса.'})
'''