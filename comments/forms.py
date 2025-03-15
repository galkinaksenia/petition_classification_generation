from django import forms
from .models import Comment
import django_filters
from django_filters import DateFilter
from django.forms.widgets import DateInput

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            'sender_name',
            'content',
            'answer',
            'status',
            'category',
            'responsible',
            'deadline'
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'sender_name': 'Отправитель',
            'content': 'Обращение',
            'answer': 'Ответ',
            'status': 'Статус',
            'category': 'Категория',
            'responsible': 'Ответственный',
            'deadline': 'Дедлайн',
        }

class CommentFilter(django_filters.FilterSet):
    sender_name = django_filters.CharFilter(field_name='sender_name', label="Отправитель", lookup_expr='icontains')
    content = django_filters.CharFilter(field_name='content', label="Обращение", lookup_expr='icontains')
    answer = django_filters.CharFilter(field_name='answer', label="Ответ", lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', label="Статус", lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category', label="Категория", lookup_expr='icontains')
    responsible = django_filters.ChoiceFilter(field_name='responsible', label="Ответственный", lookup_expr='icontains')
    created_at = django_filters.DateFilter(field_name='created_at', label="Дата создания", lookup_expr='icontains',
                                           widget=DateInput(attrs={'type': 'date'}))
    created_at_gte = DateFilter(field_name='created_at', label='Дата начала', lookup_expr='gte',
                                widget=DateInput(attrs={'type': 'date'}))
    created_at_lte = DateFilter(field_name='created_at', label='Дата окончания', lookup_expr='lte',
                                widget=DateInput(attrs={'type': 'date'}))
    deadline = django_filters.DateFilter(field_name='deadline', label="Дата создания", lookup_expr='icontains',
                                           widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Comment
        fields = [
            'sender_name',
            'content',
            'answer',
            'status',
            'category',
            'responsible',
            'created_at',
            'created_at_gte',
            'created_at_lte',
            'deadline'
        ]