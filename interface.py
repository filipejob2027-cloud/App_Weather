import os
import smtplib
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openmeteo_requests
import pandas as pd
from PIL import Image, ImageTk
import requests
import requests_cache
from retry_requests import retry as retry_session_wrapper

# Carrega variáveis de ambiente do ficheiro .env (nunca sobe ao GitHub)
load_dotenv()

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
EMAIL_ADDRESS = os.environ.get("ALERTAS_EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("ALERTAS_EMAIL_PASSWORD")


def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))


def end_fullscreen(event=None):
    root.attributes("-fullscreen", False)


def gerar_alertas(data, parametro, limite_variacao, cidade, graph_window):
    nome = {}
    unidade = {}
    if parametro == 'temperature_80m':
        nome[parametro] = "Temperatura"
        unidade[parametro] = "(ºC)"
    elif parametro == 'relative_humidity_2m':
        nome[parametro] = "Humidade"
        unidade[parametro] = "(%)"
    elif parametro == 'wind_speed_180m':
        nome[parametro] = "Velocidade do vento"
        unidade[parametro] = "(m/s)"
    elif parametro == 'pressure_msl':
        nome[parametro] = "Pressão"
        unidade[parametro] = "(hPa)"

    if data.empty:
        return

    valor_atual = data.iloc[0, -1]
    c = 0
    for valor in data.iloc[:, -1]:
        if valor < valor_atual - limite_variacao or valor > valor_atual + limite_variacao:
            _data_calend = str(data.iloc[c, 0])
            data_calend = _data_calend.split()
            dia = data_calend[0]
            hora = data_calend[1].split('+')[0].split(':')[0] + ':' + data_calend[1].split('+')[0].split(':')[1]
            sinal = "" if valor - valor_atual < 0 else "+"
            alerta_text = f"ALERTA: Grandes variações de {nome[parametro]} detectadas: {sinal}{valor - valor_atual:.2f} {unidade[parametro]} em relação a agora no dia {dia} às {hora}"
            alerta_label = tk.Label(graph_window, text=alerta_text, bg="#D3D3D3", font=("Helvetica", 16, "bold"), fg="red")
            alerta_label.pack(pady=5)
            break
        c += 1


def enviar_emails(mail, catastrofes):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Credenciais de email não configuradas (ver .env). Envio de email ignorado.")
        return

    if not catastrofes:
        mensagem = "Nenhum risco de catástrofe foi detectado com base nos dados meteorológicos."
        assunto = "Situação Controlada!"
    else:
        mensagem = "Com base nos dados meteorológicos da localidade que pesquisou, detectamos riscos de: "
        assunto = '!ALERTA!'
        for i in catastrofes:
            mensagem = mensagem + "\n" + i
    try:
        servidor = smtplib.SMTP('smtp-mail.outlook.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        email = MIMEMultipart()
        email['From'] = EMAIL_ADDRESS
        email['To'] = mail
        email['Subject'] = assunto
        email.attach(MIMEText(mensagem, 'plain'))

        servidor.sendmail(email['From'], email['To'], email.as_string())
        servidor.quit()
        print("Email enviado com sucesso!")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Erro de autenticação: {e.smtp_code}, {e.smtp_error}")
    except smtplib.SMTPException as e:
        print(f"Erro ao enviar email: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


def analizar_catastrofes(mail, dados):
    catastrofes = []
    # incêndio
    if float(dados['temperatura']) > 30 and float(dados['humidade']) < 40:
        catastrofes.append("Incêndios")
    # furacões/ciclones/tornados
    if float(dados['pressao']) < 980 and float(dados['temperatura']) > 26 and float(dados['humidade']) > 70 and float(dados['vento']) > 33:
        catastrofes.append("Tempestade (furacão/ciclone/tornado)")
    # nevascas
    if float(dados['pressao']) < 1000 and float(dados['temperatura']) < 0 and float(dados['humidade']) > 70 and float(dados['vento']) > 15:
        catastrofes.append("Nevascas")
    # ondas de frio
    if float(dados['pressao']) < 980 and float(dados['temperatura']) < 0 and float(dados['humidade']) > 70:
        catastrofes.append("Ondas de frio")
    # inundações
    if float(dados['pressao']) < 1000 and float(dados['humidade']) > 90:
        catastrofes.append("Inundações")

    enviar_emails(mail, catastrofes)


def obter_clima(cidade, chave_api):
    cidade = cidade.strip()
    if not cidade:
        messagebox.showwarning("Aviso", "Por favor, digite o nome de uma cidade.")
        return None

    if not chave_api:
        messagebox.showerror("Erro", "Chave API do OpenWeather não configurada no ficheiro .env")
        return None

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    url = f"{base_url}?q={cidade}&appid={chave_api}&units=metric&lang=pt"

    try:
        resposta = requests.get(url)
        dados = resposta.json()

        # Verifica se o código retornado pela API não é sucesso (HTTP 200)
        if resposta.status_code != 200:
            msg_erro = dados.get("message", "Erro ao obter dados da cidade.")
            messagebox.showerror("Erro na Pesquisa", f"API Erro {resposta.status_code}: {msg_erro.capitalize()}")
            return None

        # Garante que as chaves esperadas existem antes de as aceder
        coordenadas = {
            "descricao": dados["weather"][0]["description"],
            "temperatura": dados["main"]["temp"],
            "humidade": dados["main"]["humidity"],
            "pressao": dados["main"]["pressure"],
            "vento": dados["wind"]["speed"],
            "coordenadas": {
                "latitude": dados["coord"]["lat"],
                "longitude": dados["coord"]["lon"]
            }
        }
        return coordenadas

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro de Rede", f"Falha na ligação à internet: {e}")
        return None


def exibir_dados_climaticos(cidade, email):
    dados = obter_clima(cidade, OPENWEATHER_API_KEY)
    if dados:
        if email != "":
            analizar_catastrofes(email, dados)

        # Destruir widgets da página atual
        for widget in root.winfo_children():
            widget.destroy()

        # Exibir os dados básicos
        clima_label = tk.Label(root, text=f"Clima em {cidade}:\n"
                                          f"Condição: {dados['descricao']}\n"
                                          f"Temperatura : {dados['temperatura']}°C\n"
                                          f"Humidade: {dados['humidade']}%\n"
                                          f"Pressão: {dados['pressao']} hPa\n"
                                          f"Velocidade do vento: {dados['vento']} m/s",
                               bg="lightblue", font=("Helvetica", 14))
        clima_label.pack(pady=20)

        # Botão para mostrar a opção de dados avançados
        advanced_button = tk.Button(root, text="Ver Dados Avançados", command=lambda: exibir_dados_avancados(dados, cidade, email), bg="#FFD700", fg="#000000")
        advanced_button.pack(pady=10)

        voltar_button = tk.Button(root, text="Voltar", command=lambda: enter_cidade(email), bg="#FFA500", fg="#000000")
        voltar_button.place(relx=0.5, rely=0.9, anchor=tk.CENTER)


def exibir_grafico_avancado(dados, parametro, cidade):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry_session_wrapper(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    parametros = [parametro]
    params = {
        "latitude": dados['coordenadas']['latitude'],
        "longitude": dados['coordenadas']['longitude'],
        "hourly": ",".join(parametros),
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    data = {}
    dict_parametro = {
        'temperature_80m': "Temperatura",
        'relative_humidity_2m': "Humidade",
        'wind_speed_180m': "Velocidade do Vento",
        'pressure_msl': "Pressão"
    }

    if parametro in dict_parametro:
        data[parametro] = response.Hourly().Variables(0).ValuesAsNumpy()
    else:
        print("Parâmetro inválido")
        return None

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(response.Hourly().Time(), unit="s", utc=True),
            end=pd.to_datetime(response.Hourly().TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=response.Hourly().Interval()),
            inclusive="left"
        )
    }
    hourly_data[parametro] = data[parametro]
    hourly_dataframe = pd.DataFrame(data=hourly_data)
    now = pd.Timestamp(datetime.now(timezone.utc))
    hourly_dataframe = hourly_dataframe[hourly_dataframe['date'] >= now]

    alert_thresholds = {
        'temperature_80m': 10,
        'relative_humidity_2m': 40,
        'wind_speed_180m': 5,
        'pressure_msl': 10
    }

    graph_window = tk.Toplevel(root, bg='#D3D3D3')
    graph_window.attributes("-fullscreen", True)
    graph_window.bind("<Escape>", lambda event: graph_window.destroy())

    gerar_alertas(hourly_dataframe, parametro, alert_thresholds[parametro], cidade, graph_window)

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(hourly_dataframe['date'], hourly_dataframe[parametro], label=dict_parametro[parametro])
    ax.set_xlabel('Data e Hora')
    ax.set_ylabel(dict_parametro[parametro])
    ax.set_title(f'Variação de {dict_parametro[parametro]} ao Longo do Tempo')
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()

    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    close_button = tk.Button(graph_window, text="Fechar", command=graph_window.destroy, bg="#FFA500", fg="#000000")
    close_button.pack(pady=10)


def exibir_dados_avancados(dados, cidade, email):
    for widget in root.winfo_children():
        widget.destroy()

    num_rows = 1
    data_inicial = pd.Timestamp.now()
    intervalo = pd.Timedelta(hours=1)
    dados['date'] = [data_inicial + i * intervalo for i in range(num_rows)]

    temperature_button = tk.Button(root, text="Temperatura", command=lambda: exibir_grafico_avancado(dados, 'temperature_80m', cidade), bg="#FFD700", fg="#000000")
    temperature_button.pack(pady=5)
    humidity_button = tk.Button(root, text="Humidade", command=lambda: exibir_grafico_avancado(dados, 'relative_humidity_2m', cidade), bg="#FFD700", fg="#000000")
    humidity_button.pack(pady=5)
    pressure_button = tk.Button(root, text="Pressão", command=lambda: exibir_grafico_avancado(dados, 'pressure_msl', cidade), bg="#FFD700", fg="#000000")
    pressure_button.pack(pady=5)
    wind_speed_button = tk.Button(root, text="Velocidade do Vento", command=lambda: exibir_grafico_avancado(dados, 'wind_speed_180m', cidade), bg="#FFD700", fg="#000000")
    wind_speed_button.pack(pady=5)
    voltar_button = tk.Button(root, text="Voltar", command=lambda: exibir_dados_climaticos(cidade, email), bg="#FFA500", fg="#000000")
    voltar_button.pack(pady=5)


def on_button_click():
    button.place_forget()
    button1 = tk.Button(root, text="Entrar com correio eletrónico", command=enter_with_email, bg="#FFD700", fg="#000000")
    button1.place(relx=0.4, rely=0.5, anchor=tk.CENTER)
    button2 = tk.Button(root, text="Entrar sem correio eletrónico", command=enter_without_email, bg="#FFD700", fg="#000000")
    button2.place(relx=0.6, rely=0.5, anchor=tk.CENTER)


def enter_without_email():
    email = ""
    enter_cidade(email)


def enter_with_email():
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button):
            widget.place_forget()
    email_label = tk.Label(root, text="Insira seu email:", bg="lightblue")
    email_label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
    email_entry = tk.Entry(root)
    email_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    submit_button = tk.Button(root, text="Enviar", command=lambda: submit_email(email_entry.get()), bg="#FFD700", fg="#000000")
    submit_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)


def submit_email(email):
    for widget in root.winfo_children():
        if isinstance(widget, (tk.Entry, tk.Label, tk.Button)):
            widget.place_forget()
    confirmation_label = tk.Label(root, text=f"Email '{email}' enviado com sucesso!", bg="lightblue")
    confirmation_label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
    prosseguir = tk.Button(root, text="Continuar", command=lambda: enter_cidade(email), bg="green", fg="#000000")
    prosseguir.place(relx=0.5, rely=0.6, anchor=tk.CENTER)


def enter_cidade(email):
    for widget in root.winfo_children():
        widget.destroy()

    try:
        my_label = tk.Label(root, image=my_img)
        my_label.place(x=0, y=0)
    except NameError:
        pass

    city_label = tk.Label(root, text="Insira a cidade:", bg="lightblue")
    city_label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
    city_entry = tk.Entry(root)
    city_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    city_submit_button = tk.Button(root, text="Obter Dados Climáticos", command=lambda: exibir_dados_climaticos(city_entry.get(), email), bg="#FFD700", fg="#000000")
    city_submit_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)


root = tk.Tk()
root.title("Minha Primeira Interface")
root.attributes("-fullscreen", True)
root.bind("<Escape>", end_fullscreen)
root.bind("<F11>", toggle_fullscreen)
root.config(bg="lightblue")

label = tk.Label(root, text="", bg="lightblue")
label.pack(pady=10)

try:
    my_img = ImageTk.PhotoImage(Image.open("u.jpg"))
    my_label = tk.Label(root, image=my_img)
    my_label.place(x=0, y=0)
except FileNotFoundError:
    print("Imagem 'u.jpg' não encontrada.")

button = tk.Button(root, text="Menu", command=on_button_click, bg="#FFFF00", fg="#00008B")
button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

root.mainloop()