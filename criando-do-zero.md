# Sistema de Gerenciamento de Pedidos - Django

# Instale o Redis
 - Instalador em https://github.com/tporadowski/redis/releases
 - Marque a caixa de adicionar o executável ao PATH do windows

# Instale o wkhtmltopdf:
 - Windows: https://wkhtmltopdf.org/downloads.html
 - Linux: sudo apt install wkhtmltopdf
 Obs.: Caso encontre o erro: `OSError at /relatorios/pdf/2
    No wkhtmltopdf executable found: "b''"
    If this file exists please check that this process can read it or you can pass path to it manually in method call, check README. Otherwise please install wkhtmltopdf - https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf`
 -> Verifique a pasta de instalação e a inclua nas variáveis de ambiente do sistema como mosta o [print](./variaveis-ambiente.png)


## 1️⃣ Criação do Projeto
```bash
django-admin startproject core .
# OU
# python -m django startproject core .
python manage.py startapp produtos
python manage.py startapp pedidos
python manage.py startapp relatorios
```

Adicione as apps no `settings.py`:
```python
INSTALLED_APPS = [
    ...,
    'produtos',
    'pedidos',
    'relatorios',
]

# Nesse trecho apenas adicione 'core/templates' na lista de DIRS
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['core/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Adicione no início:

import os
from dotenv import load_dotenv
load_dotenv()

# Adicione no final:
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_PEDIDO_DESTINO = os.getenv('EMAIL_PEDIDO_DESTINO')

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
```

### Crie um arquivo `.env` dentro da pasta `core`:
```env
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST='smtp.zoho.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<PERGUNTE AO PROFESSOR>
EMAIL_HOST_PASSWORD=<PERGUNTE AO PROFESSOR>
DEFAULT_FROM_EMAIL=<PERGUNTE AO PROFESSOR>
EMAIL_PEDIDO_DESTINO=<COLOQUE UM EMAIL SEU PARA RECEBER>
```

##  Modelos (models.py)
**produtos/models.py**
```python
from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    estoque = models.IntegerField()

    def __str__(self):
        return f"{self.nome} - Estoque: {self.estoque}"
```

**pedidos/models.py**
```python
from django.db import models
from produtos.models import Produto

class Pedido(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    data_pedido = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido de {self.quantidade}x {self.produto.nome}"
```

##  Forms
**produtos/forms.py**
```python
from django import forms
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'estoque']
```

**pedidos/forms.py**
```python
from django import forms
from .models import Pedido

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['produto', 'quantidade']
```

## Signal para atualizar estoque
**pedidos/signals.py**
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from pedidos.models import Pedido
from pedidos.tasks import task_atualizar_estoque


@receiver(post_save, sender=Pedido)
def signal_atualizar_estoque(sender, instance, created, **kwargs):
    if created:
        def disparar_task():
            celery_task = task_atualizar_estoque.apply_async((instance.id,), countdown=1)
            if celery_task and celery_task.id:
                print(f'Task agendada para atualização de estoque {celery_task.id}')

        transaction.on_commit(disparar_task)
```

**pedidos/apps.py** (registrar o signal)
```python
from django.apps import AppConfig

class PedidosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pedidos'

    def ready(self):
        import pedidos.signals
```

## 5️⃣ Views
**produtos/views.py**
```python
from django.shortcuts import render, redirect
from .models import Produto
from .forms import ProdutoForm

def cadastrar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProdutoForm()
    return render(request, 'produtos/cadastrar.html', {'form': form})

def lista_produtos(request):
    produtos = Produto.objects.all()
    return render(request, 'produtos/lista.html', {'produtos': produtos})
```

**pedidos/views.py**
```python
from django.shortcuts import render, redirect
from .models import Pedido
from .forms import PedidoForm

def cadastrar_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pedidos')
    else:
        form = PedidoForm()
    return render(request, 'pedidos/cadastrar.html', {'form': form})

def lista_pedidos(request):
    pedidos = Pedido.objects.all()
    return render(request, 'pedidos/lista.html', {'pedidos': pedidos})
```
**relatorios/views.py**
```python
from django.http import HttpResponse
from django.views import View
from django.template.loader import render_to_string
from pedidos.models import Pedido
from django.utils.timezone import localtime
import io
from reportlab.pdfgen import canvas
import pdfkit

class ExportarPedidosPDFView(View):
    def get(self, request, *args, **kwargs):
        metodo = request.GET.get('metodo', '1')

        if metodo == '2':
            return self.gerar_pdf_pdfkit()
        return self.gerar_pdf_reportlab()

    def gerar_pdf_reportlab(self):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        pedidos = Pedido.objects.select_related('produto').all()

        y = 800
        p.setFont("Helvetica", 12)
        p.drawString(100, y, "Lista de Pedidos (ReportLab):")
        y -= 30

        for pedido in pedidos:
            texto = f"{localtime(pedido.data_pedido).strftime('%d/%m/%Y %H:%M')} - {pedido.quantidade}x {pedido.produto.nome}"
            p.drawString(100, y, texto)
            y -= 20
            if y < 50:
                p.showPage()
                y = 800

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pedidos_reportlab.pdf"'
        return response

    def gerar_pdf_pdfkit(self):
        pedidos = Pedido.objects.select_related('produto').all()
        html = render_to_string('relatorios/relatorio_pdf.html', {'pedidos': pedidos})
        pdf = pdfkit.from_string(html, False)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pedidos_pdfkit.pdf"'
        return response
```


## 6️⃣ Templates
**base.html**
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container">
            <a class="navbar-brand" href="/">Gestão de Pedidos</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/produtos/">Produtos</a>
                <a class="nav-link" href="/pedidos/">Pedidos</a>
            </div>
        </div>
    </nav>
    <div class="container mt-5">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

**produtos/cadastrar.html**
```html
{% extends 'base.html' %}
{% block content %}
    <h2>Cadastrar produto</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Salvar</button>
    </form>
{% endblock %}
```

**pedidos/cadastrar.html**
```html
{% extends 'base.html' %}
{% block content %}
    <h2>Cadastrar pedido</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Salvar Pedido</button>
    </form>
{% endblock %}
```

**relatorios/relatorio_pdf.html**
```html
{% load tz %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Pedidos</title>
</head>
<body>
    <h1>Lista de Pedidos (pdfkit)</h1>
    <ul>
    {% for pedido in pedidos %}
        <li>{{ pedido.data_pedido|localtime|date:"d/m/Y H:i" }} - {{ pedido.quantidade }}x {{ pedido.produto.nome }}</li>
    {% endfor %}
    </ul>
</body>
</html>
```


## URLs
**core/urls.py**
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('produtos/', include('produtos.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('relatorios/', include('relatorios.urls')),
]
```

**produtos/urls.py**
```python
from django.urls import path
from .views import cadastrar_produto, lista_produtos

urlpatterns = [
    path('cadastrar/', cadastrar_produto, name='cadastrar_produto'),
    path('', lista_produtos, name='lista_produtos'),
]
```

**pedidos/urls.py**
```python
from django.urls import path
from .views import cadastrar_pedido, lista_pedidos

urlpatterns = [
    path('cadastrar/', cadastrar_pedido, name='cadastrar_pedido'),
    path('', lista_pedidos, name='lista_pedidos'),
]
```

**relatorios/urls.py**
```python
from django.urls import path
from .views import ExportarPedidosPDFView

urlpatterns = [
    path('pdf/<str:metodo>', ExportarPedidosPDFView.as_view(), name='exportar_pedidos_pdf'),
]
```

## Configurar celery no projeto
- Crie o arquivo `celery.py` dentro de `core`
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

- Edite o arquivo `core/__init__.py`
```python
from .celery import app as celery_app
__all__ = ('celery_app',)

```

## Migrações de banco de dados
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Em outro console inicie o worker celery para consumir e executar as tarefas:

```bash
celery -A core worker --loglevel=info --concurrency=1 --pool=solo
```

## Se quiser acompanhar a execução das tasks
- Instale o flower
```bash
pip install flower
```
- E rode o servidor flower, depois acesse: `http://localhost:5555`
```bash
celery -A core flower --port=5555
```

## Testes
Acesse `/produtos/` para cadastrar produtos e `/pedidos/` para realizar pedidos e ver a atualização do estoque em tempo real além do envio do e-mail em segundo plano (sem prender a requisição de cadastro de pedido)!

## Acesse `http://127.0.0.1:8000/relatorios/pdf/1` e `http://127.0.0.1:8000/relatorios/pdf/2` para obter o arquivo pdf como download.
Obs.: Tem dois métodos de exportação para pdf implementados