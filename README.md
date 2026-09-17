# 🌤️ Weather Monitoring & Disaster Alert System

Uma aplicação desktop desenvolvida em **Python** para consulta meteorológica em tempo real, visualização avançada de previsões em séries temporais e emissão automática de alertas de risco de catástrofes naturais via e-mail.

---

## 📋 Índice
- [Visão Geral](#-visão-geral)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Arquitetura e Tecnologias](#-arquitetura-e-tecnologias)
- [Lógica do Motor de Alertas](#-lógica-do-motor-de-alertas)
- [Pré-requisitos e Dependências](#-pré-requisitos-e-dependências)
- [Configuração e Instalação](#-configuração-e-instalação)
- [Como Utilizar](#-como-utilizar)
- [Estrutura do Ficheiro .env](#-estrutura-do-ficheiro-env)

---

## 🌤️ Visão Geral

O **Weather Monitoring & Disaster Alert System** é uma solução completa em Python com interface gráfica que agrega dados de múltiplas APIs meteorológicas externas. A aplicação processa métricas em tempo real (temperatura, humidade, pressão atmosférica e velocidade do vento), gera gráficos interativos com séries temporais de previsão e analisa continuamente os valores para identificar variações bruscas ou condições favoráveis a catástrofes naturais, notificando o utilizador por e-mail de forma autónoma.

---

## 🚀 Funcionalidades Principais

* **Consulta Meteorológica em Tempo Real:**
  * Integração com a **OpenWeather API** para recolha instantânea de condições climatológicas por cidade.
  * Validação e tratamento de erros de ligação ou cidade não encontrada.

* **Motor de Análise de Catástrofes Naturais:**
  * Algoritmo paramétrico que avalia combinações de fatores climáticos para identificar potenciais riscos de incêndios, tempestades/ciclones, nevascas, ondas de frio e inundações.
  * Envio automático de relatórios de risco para o e-mail do utilizador via **SMTP (Outlook/Hotmail)**.

* **Análise Avançada e Séries Temporais:**
  * Consulta à **Open-Meteo API** para obter previsões horárias detalhadas.
  * Renderização de gráficos nativos de variação temporal (Temperatura, Humidade, Pressão e Vento) em ecrã inteiro com **Matplotlib** integrado na interface **Tkinter**.

* **Deteção de Variações Bruscas:**
  * Algoritmo de auditoria de dados que identifica flutuações acentuadas em relação ao momento atual e desenha avisos destacados sobre os gráficos.

* **Resiliência e Desempenho:**
  * Sistema de cache de pedidos HTTP (`requests_cache`) com tempo de expiração programado (1 hora).
  * Mecanismo de re-tentativa (`retry_requests`) com *backoff* exponencial em caso de instabilidade na API.
  * Gestão segura de credenciais sensíveis através de variáveis de ambiente (`python-dotenv`).

---

## 🛠️ Arquitetura e Tecnologias

* **Linguagem:** Python 3.x
* **Interface Gráfica (GUI):** `tkinter`, `PIL` (Pillow)
* **Processamento de Dados:** `pandas`, `numpy`
* **Visualização de Dados:** `matplotlib` (`FigureCanvasTkAgg`)
* **Consumo de APIs REST:** `requests`, `openmeteo-requests`, `requests-cache`, `retry-requests`
* **Comunicação por E-mail:** `smtplib`, `email.mime`
* **Segurança e Variáveis de Ambiente:** `python-dotenv`

---

## ⚠️ Lógica do Motor de Alertas

O sistema analisa os dados recolhidos e aciona alertas de e-mail segundo as seguintes regras de negócio:

| Catástrofe | Condições Meteorológicas Requeridas |
| :--- | :--- |
| **Incêndios** | Temperatura > 30 ºC **E** Humidade < 40 % |
| **Tempestade / Ciclone / Tornado** | Pressão < 980 hPa **E** Temperatura > 26 ºC **E** Humidade > 70 % **E** Vento > 33 m/s |
| **Nevascas** | Pressão < 1000 hPa **E** Temperatura < 0 ºC **E** Humidade > 70 % **E** Vento > 15 m/s |
| **Ondas de Frio** | Pressão < 980 hPa **E** Temperatura < 0 ºC **E** Humidade > 70 % |
| **Inundações** | Pressão < 1000 hPa **E** Humidade > 90 % |

---

## 📦 Pré-requisitos e Dependências

Para executar esta aplicação, garante que tens o Python 3.8 ou superior instalado.

Cria um ficheiro chamado `requirements.txt` com as seguintes dependências:

```text
requests
pandas
matplotlib
pillow
python-dotenv
openmeteo-requests
requests-cache
retry-requests
