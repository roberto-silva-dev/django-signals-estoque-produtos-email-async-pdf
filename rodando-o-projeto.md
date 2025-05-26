## 🚀 Rodando o Projeto

1️⃣ Clone o repositório:  
```bash
git clone https://github.com/roberto-silva-dev/django-signals-estoque-produtos-email-async-pdf.git
cd core
```

2️⃣ Instale as dependências:  
```bash
pip install -r requirements.txt
```
# Instale o Redis pelo link: `https://github.com/tporadowski/redis/releases` ou direto no site oficial `https://redis.io`

# Instale o wkhtmltopdf:
 - Windows: https://wkhtmltopdf.org/downloads.html
 - Linux: sudo apt install wkhtmltopdf
 Obs.: Caso encontre o erro: `OSError at /relatorios/pdf/2
    No wkhtmltopdf executable found: "b''"
    If this file exists please check that this process can read it or you can pass path to it manually in method call, check README. Otherwise please install wkhtmltopdf - https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf`
 -> Verifique a pasta de instalação e a inclua nas variáveis de ambiente do sistema como mosta o [print](./variaveis-ambiente.png)

### Configre o arquivo .env com as credenciais do servidor de e-mail

3️⃣ Realize as migrações:  
```bash
python manage.py makemigrations
python manage.py migrate
```

4️⃣ Rode o servidor:  
```bash
python manage.py runserver
```

Acesse o sistema: [http://127.0.0.1:8000](http://127.0.0.1:8000)


- Rode o consumidor de tarefas (worker)
```bash
celery -A core worker --loglevel=info --concurrency=1 --pool=solo
```

- Rode o flower para acompanhar a execução das tarefas
```bash
celery -A core flower --port=5555
```
Acesse em `http://localhost:5555`

