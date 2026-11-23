<div align="center">

# AssetSlicer API

**API que fatia spritesheets em assets individuais e remove o fundo automaticamente.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8?logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?logo=numpy&logoColor=white)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](./LICENSE)

</div>

---

## 📖 Sobre

A **AssetSlicer API** é um serviço em **Python** construído com **FastAPI** que recebe uma imagem no formato *spritesheet* (uma grade de sprites em um único arquivo), recorta cada célula da grade como um asset individual e remove automaticamente o fundo, devolvendo todos os recortes empacotados em um arquivo ZIP.

Toda a lógica de processamento de imagem usa **OpenCV** e **NumPy** e roda inteiramente em memória — nenhuma imagem é gravada em disco. O algoritmo segmenta a grade em células, identifica o fundo pela distância de cor em relação a um RGB configurável, isola o maior contorno de cada célula (o sprite), aplica um filtro anti-serrilhado (erosão e desfoque Gaussiano) para gerar um canal alfa suave e recorta o sprite com uma margem de segurança.

É destinada a artistas, desenvolvedores de jogos e criadores de conteúdo que precisam separar spritesheets em arquivos PNG avulsos com transparência de forma automatizada. O serviço está pronto para implantação em plataformas como o **Render**, com arquivos de configuração de deploy incluídos.

## ✨ Funcionalidades

- Endpoint `POST /process` que recebe a imagem via `multipart/form-data` e devolve um ZIP com os assets separados.
- Segmentação do spritesheet em grade configurável (linhas e colunas).
- Remoção de fundo por cor RGB configurável com tolerância ajustável.
- Filtro anti-serrilhado na máscara (erosão + desfoque Gaussiano) convertido em canal alfa, gerando bordas suaves.
- Recorte justo ao redor do sprite (bounding box) com padding de segurança e padding final configuráveis.
- Descarte automático de células vazias (sem contornos detectados).
- Conversão automática da imagem para o formato com canal alfa (BGRA), aceitando entrada em escala de cinza, BGR ou BGRA.
- Empacotamento dos assets em ZIP em memória e resposta via streaming, com `prefix_row_col.png` como padrão de nomenclatura.
- Validação do tipo de arquivo enviado (precisa ser uma imagem).
- Tratamento de erros com respostas HTTP apropriadas (imagem inválida ou nenhum asset encontrado).
- CORS liberado para todas as origens.
- Endpoint de verificação de saúde `GET /health`.
- Configuração de deploy para o Render (`render.yaml`) e `Procfile` para plataformas do tipo Heroku.

## 🛠️ Tecnologias

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.34-6DA544?logo=uvicorn&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8?logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?logo=numpy&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)

## 📁 Estrutura do projeto

```
assetslicer-api/
├── main.py            # aplicação FastAPI e lógica de fatiamento com OpenCV
├── requirements.txt   # dependências do projeto
├── render.yaml        # configuração de deploy no Render
├── Procfile           # comando de start (plataformas tipo Heroku)
└── README.md
```

## 🚀 Como rodar localmente

```bash
# Criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Instalar as dependências
pip install -r requirements.txt

# Iniciar o servidor de desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API ficará disponível em `http://localhost:8000/`. Os principais endpoints são:

- `POST /process` — envia a imagem e os parâmetros do fatiamento; retorna o ZIP.
- `GET /health` — verifica se o serviço está no ar.

## 📄 Licença

Distribuído sob a **Licença MIT**. Veja [`LICENSE`](./LICENSE).
