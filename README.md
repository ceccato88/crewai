# 🤖 CrewAI Multimodal System - Sistema Completo de Análise Textual e Visual

> Um sistema avançado de IA que combina análise de texto via embeddings e análise visual real usando CrewAI, VoyageAI e GPT-4o

[![CrewAI](https://img.shields.io/badge/CrewAI-Latest-blue)](https://github.com/joaomdmoura/crewai)
[![Python](https://img.shields.io/badge/Python-3.12+-green)](https://python.org)
[![VoyageAI](https://img.shields.io/badge/VoyageAI-Multimodal-orange)](https://voyageai.com)
[![Async](https://img.shields.io/badge/Async-Supported-purple)](https://docs.python.org/3/library/asyncio.html)

## 📋 Índice

1. [O que é este Sistema?](#-o-que-é-este-sistema)
2. [Características Principais](#-características-principais)
3. [Pré-requisitos](#-pré-requisitos)
4. [Instalação Passo a Passo](#-instalação-passo-a-passo)
5. [Configuração de API Keys](#-configuração-de-api-keys)
6. [Como Usar](#-como-usar)
7. [Exemplos Práticos](#-exemplos-práticos)
8. [Estrutura do Projeto](#-estrutura-do-projeto)
9. [Resolução de Problemas](#-resolução-de-problemas)
10. [Conceitos Técnicos](#-conceitos-técnicos)
11. [FAQ](#-faq)

## 🎯 O que é este Sistema?

Este sistema é uma implementação avançada de **análise multimodal** usando CrewAI que pode:

- 📝 **Analisar textos** usando embeddings semânticos (VoyageAI)
- 👁️ **Ver e analisar imagens** usando visão computacional (GPT-4o)
- 🧠 **Coordenar análises** integrando insights textuais e visuais
- ⚡ **Executar paralelamente** múltiplas análises simultaneamente
- 🎯 **Trabalhar hierarquicamente** com manager automático

### 💡 Para que serve?

- Analisar documentos que contêm texto + imagens
- Extrair insights de relatórios visuais
- Processar conteúdo multimodal automaticamente
- Gerar análises coordenadas texto + visual

## ✨ Características Principais

### 🔥 **Análise Multimodal Real**
- ✅ Análise textual via embeddings VoyageAI
- ✅ Análise visual real (não especulação)
- ✅ Síntese coordenada dos insights

### ⚡ **Execução Assíncrona**
- ✅ `kickoff_async()` para execução não-bloqueante
- ✅ Múltiplas crews em paralelo
- ✅ Performance otimizada

### 🎯 **Processo Hierárquico**
- ✅ Manager automático coordena agentes
- ✅ Delegação inteligente de tarefas
- ✅ Três agentes especializados

### 🛠️ **Agentes Especializados**
1. **Pesquisador de Texto** - Analisa metadados markdown
2. **Analista Visual** - Vê e analisa imagens reais  
3. **Coordenador Multimodal** - Integra ambas as análises

## 🔧 Pré-requisitos

### Sistema
- **Python 3.12+** (recomendado 3.12.1)
- **pip** (gerenciador de pacotes Python)
- **Git** (opcional, para clonagem)

### APIs Necessárias
1. **OpenAI API** - Para GPT-4o (análise visual e coordenação)
2. **VoyageAI API** - Para embeddings multimodais
3. **Upstash Vector** - Para busca semântica (base de dados vetorial)

### Conhecimento Básico
- Como usar terminal/prompt de comando
- Conceitos básicos de Python (opcional)
- Como obter API keys

## 🚀 Instalação Passo a Passo

### Passo 1: Clone ou Baixe o Projeto

#### Opção A: Com Git
```bash
git clone <URL_DO_REPOSITORIO>
cd crewai
```

#### Opção B: Download ZIP
1. Baixe o arquivo ZIP do projeto
2. Extraia para uma pasta (ex: `C:\crewai` ou `~/crewai`)
3. Abra terminal na pasta do projeto

### Passo 2: Crie um Ambiente Virtual Python

#### No Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### No Mac/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> 💡 **Dica**: Você deve ver `(.venv)` no início da linha do terminal quando ativado

### Passo 3: Instale as Dependências

```bash
pip install --upgrade pip
pip install crewai crewai-tools
pip install upstash-vector voyageai
pip install python-dotenv
```

### Passo 4: Verifique a Instalação

```bash
python -c "import crewai; print('CrewAI instalado com sucesso!')"
```

## 🔑 Configuração de API Keys

### 1. Obtenha as API Keys

#### OpenAI API Key
1. Acesse [platform.openai.com](https://platform.openai.com)
2. Faça login ou crie uma conta
3. Vá em "API Keys" → "Create new secret key"
4. Copie a chave (começa com `sk-`)

#### VoyageAI API Key
1. Acesse [voyageai.com](https://voyageai.com)
2. Faça cadastro/login
3. Vá na seção API Keys
4. Gere uma nova chave

#### Upstash Vector Database
1. Acesse [upstash.com](https://upstash.com)
2. Crie uma conta gratuita
3. Crie um novo Vector Database
4. Copie a URL e Token da base criada

### 2. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Crie o arquivo .env
touch .env  # Mac/Linux
echo. > .env  # Windows
```

Abra o arquivo `.env` em um editor de texto e adicione:

```env
# OpenAI (necessário)
OPENAI_API_KEY=sk-sua_chave_openai_aqui

# VoyageAI (necessário)
VOYAGE_API_KEY=sua_chave_voyage_aqui

# Upstash Vector (necessário)
UPSTASH_VECTOR_REST_URL=https://sua-url.upstash.io
UPSTASH_VECTOR_REST_TOKEN=seu_token_upstash_aqui
```

> ⚠️ **IMPORTANTE**: Nunca compartilhe suas API keys! O arquivo `.env` já está no `.gitignore`

### 3. Teste a Configuração

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ OpenAI:', 'Configurado' if os.getenv('OPENAI_API_KEY') else '❌ Faltando')
print('✅ VoyageAI:', 'Configurado' if os.getenv('VOYAGE_API_KEY') else '❌ Faltando')
print('✅ Upstash URL:', 'Configurado' if os.getenv('UPSTASH_VECTOR_REST_URL') else '❌ Faltando')
print('✅ Upstash Token:', 'Configurado' if os.getenv('UPSTASH_VECTOR_REST_TOKEN') else '❌ Faltando')
"
```

## 🎮 Como Usar

### Uso Básico (Síncrono)

```bash
# Análise simples
python src/main.py "Analise este documento"

# Com pergunta específica
python src/main.py "Resuma o conteúdo e descreva as imagens"
```

### Uso Avançado (Assíncrono)

```bash
# Execução assíncrona
python src/main.py "o que é o zep?" --async

# Demo completo das capacidades assíncronas
python async_demo.py --quick

# Comparação sequencial vs paralelo
python async_demo.py --compare

# Teste de stress (cuidado com limites de API)
python async_demo.py --stress
```

### Interface Python

```python
# Síncrono
from src.generic_mm_project.crew import GenericMMCrew

crew = GenericMMCrew().crew()
result = crew.kickoff(inputs={"query": "Sua pergunta"})
print(result.raw)

# Assíncrono
import asyncio

async def main():
    result = await crew.kickoff_async(inputs={"query": "Sua pergunta"})
    print(result.raw)

asyncio.run(main())
```

## 📚 Exemplos Práticos

### Exemplo 1: Análise de Documento Simples
```bash
python src/generic_mm_project/main.py "Faça um resumo executivo do documento"
```

**O que acontece:**
1. 🔍 Pesquisador busca texto relevante na base vetorial
2. 👁️ Analista visual examina imagens relacionadas
3. 🧠 Coordenador integra ambas as análises
4. 📄 Gera relatório final em `output/multimodal_report.md`

### Exemplo 2: Foco em Análise Visual
```bash
python src/generic_mm_project/main.py "Descreva detalhadamente todas as imagens e gráficos"
```

### Exemplo 3: Comparação de Dados
```bash
python src/generic_mm_project/main.py "Compare os dados quantitativos mencionados no texto com os gráficos visuais"
```

### Exemplo 4: Execução Paralela
```bash
# Demo rápido de execução paralela
python async_demo.py --quick
```

### Exemplo 5: Múltiplas Análises
```python
import asyncio
from src.generic_mm_project.main import run_multiple_queries_async

async def main():
    queries = [
        "Analise aspectos técnicos",
        "Foque nos dados visuais", 
        "Extraia conclusões gerais"
    ]
    results = await run_multiple_queries_async(queries)
    for i, result in enumerate(results):
        print(f"Análise {i+1}: {result.raw[:200]}...")

asyncio.run(main())
```

## 📁 Estrutura do Projeto

```
crewai/
├── 📄 README.md                    # Este arquivo
├── 📄 .env                        # Suas API keys (criar)
├── 📄 async_demo.py               # Demo das capacidades assíncronas
├── 📁 src/generic_mm_project/
│   ├── 📄 main.py                 # Script principal
│   ├── 📄 crew.py                 # Definição dos agentes e crew
│   ├── 📄 upstash_vector_tool.py  # Ferramenta de busca vetorial
│   ├── 📄 voyage_embed.py         # Embeddings VoyageAI
│   └── 📁 config/
│       ├── 📄 agents.yaml         # Configuração dos agentes
│       └── 📄 tasks.yaml          # Configuração das tarefas
├── 📁 test_images/                # Imagens de teste
│   ├── 🖼️ diagram1.png
│   ├── 🖼️ diagram2.png
│   └── 🖼️ diagram3.png
└── 📁 output/                     # Relatórios gerados
    └── 📄 multimodal_report.md
```

### Arquivos Principais

#### `main.py` 
- Script principal para execução
- Suporte síncrono e assíncrono
- Interface de linha de comando

#### `crew.py`
- Define os 3 agentes especializados
- Configura processo hierárquico
- Gerencia fluxo de tarefas

#### `config/agents.yaml`
- Configurações dos agentes (roles, goals, backstory)
- Especifica modelos LLM e capacidades multimodais

#### `config/tasks.yaml`
- Define as 3 tarefas principais
- Especifica formato de entrada/saída
- Configura dependências entre tarefas

## 🔧 Resolução de Problemas

### ❌ Problema: "ModuleNotFoundError: No module named 'crewai'"

**Solução:**
```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Mac/Linux
# ou
.venv\Scripts\activate     # Windows

# Reinstale
pip install crewai crewai-tools
```

### ❌ Problema: "API key not found"

**Solução:**
1. Verifique se o arquivo `.env` existe
2. Verifique se as chaves estão corretas
3. Reinicie o terminal após criar `.env`

```bash
# Teste suas chaves
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('OpenAI:', os.getenv('OPENAI_API_KEY', 'NÃO ENCONTRADA')[:10] + '...')
"
```

### ❌ Problema: "Rate limit exceeded"

**Solução:**
- Aguarde alguns minutos entre execuções
- Para demos de stress, use `--quick` em vez de `--stress`
- Verifique limites da sua conta OpenAI/VoyageAI

### ❌ Problema: "Upstash connection failed"

**Solução:**
1. Verifique se URL e Token estão corretos
2. Confirme se o banco vetorial está ativo no Upstash
3. Teste conectividade:

```bash
python -c "
from upstash_vector import Index
import os
from dotenv import load_dotenv
load_dotenv()
try:
    index = Index(url=os.getenv('UPSTASH_VECTOR_REST_URL'), token=os.getenv('UPSTASH_VECTOR_REST_TOKEN'))
    print('✅ Conexão Upstash OK')
except Exception as e:
    print(f'❌ Erro Upstash: {e}')
"
```

### ❌ Problema: "Images not being analyzed properly"

**Solução:**
1. Verifique se as imagens existem em `test_images/`
2. Use caminhos absolutos para suas próprias imagens
3. Certifique que o agente tem `multimodal: true`

### ❌ Problema: Execução muito lenta

**Solução:**
- Use execução assíncrona: `--async`
- Para múltiplas análises, use `async_demo.py --quick`
- Evite fazer muitas chamadas simultâneas

## 🧠 Conceitos Técnicos

### O que é CrewAI?

CrewAI é um framework para orquestrar múltiplos agentes de IA que trabalham juntos como uma equipe. Cada agente tem:

- **Role** (papel): O que o agente faz
- **Goal** (objetivo): O que ele busca alcançar  
- **Backstory** (história): Contexto e especialidade
- **Tools** (ferramentas): O que pode usar para executar tarefas

### Processo Hierárquico vs Sequencial

#### Sequencial
```
Agente 1 → Agente 2 → Agente 3
(um de cada vez)
```

#### Hierárquico
```
    Manager
   /   |   \
  A1   A2   A3
(pode executar em paralelo)
```

### Embeddings Multimodais

**Embeddings** são representações numéricas de texto que capturam significado semântico. O VoyageAI `voyage-multimodal-3` pode criar embeddings que entendem tanto texto quanto imagens.

### Upstash Vector Database

Base de dados vetorial que armazena embeddings e permite busca semântica ultra-rápida. Quando você pergunta algo, o sistema:

1. Converte sua pergunta em embedding
2. Busca embeddings similares na base
3. Retorna conteúdo relevante

### Análise Visual Real

O agente usa GPT-4o com `AddImageTool` para realmente "ver" imagens:

```python
# O agente REALMENTE vê a imagem
resultado = agent.analyze_image("/path/to/image.png")
# vs especular sobre ela
```

## ❓ FAQ

### P: Preciso saber programar para usar?

**R:** Não! Você pode usar via linha de comando:
```bash
python src/generic_mm_project/main.py "Sua pergunta aqui"
```

### P: Quanto custa usar este sistema?

**R:** Depende do uso das APIs:
- **OpenAI GPT-4o**: ~$0.005 por 1K tokens de input
- **VoyageAI**: ~$0.00012 por 1K tokens  
- **Upstash**: Plano gratuito para testes

Uma análise típica custa centavos.

### P: Posso usar minhas próprias imagens?

**R:** Sim! Modifique a tarefa de análise visual em `config/tasks.yaml` para incluir caminhos para suas imagens.

### P: Funciona offline?

**R:** Não, precisa de internet para acessar as APIs (OpenAI, VoyageAI, Upstash).

### P: Posso usar outros modelos além do GPT-4o?

**R:** Sim! Modifique os arquivos de configuração:

```yaml
# config/agents.yaml
text_researcher:
  llm: anthropic/claude-3-sonnet  # Exemplo
```

### P: Como adiciono mais agentes?

**R:** 
1. Adicione novo agente em `config/agents.yaml`
2. Crie método correspondente em `crew.py`
3. Adicione tarefas em `config/tasks.yaml`

### P: O sistema funciona em português?

**R:** Sim! Todos os prompts e configurações estão em português. Os modelos de IA entendem perfeitamente.

### P: Posso integrar com meu sistema existente?

**R:** Sim! Use como biblioteca Python:

```python
from src.generic_mm_project.crew import GenericMMCrew
# Integre em sua aplicação
```

### P: Como customizo as análises?

**R:** Modifique os arquivos YAML:
- `config/agents.yaml` - Personalidades e especialidades dos agentes
- `config/tasks.yaml` - Instruções específicas e formatos de saída

### P: Onde ficam salvos os resultados?

**R:** No diretório `output/multimodal_report.md` após cada execução.

## 🆘 Suporte

### Se algo não funcionar:

1. **Verifique os pré-requisitos** - Python 3.12+, APIs configuradas
2. **Consulte a seção de problemas** acima
3. **Teste a configuração** com os comandos fornecidos
4. **Execute um exemplo simples** primeiro

### Logs e Debug

Para ver mais detalhes durante execução:
```bash
# Modo verbose
python src/generic_mm_project/main.py "Sua pergunta" --debug
```

### Estrutura de Suporte

```
🔍 Problema Simples → Seção "Resolução de Problemas"
🔧 Problema Técnico → Verifique configuração APIs  
💡 Dúvida de Uso → Seção FAQ
🚀 Customização → Modifique arquivos YAML
```

---

## 🎉 Pronto para Começar!

Agora você tem tudo que precisa para usar este sistema avançado de análise multimodal. Comece com um exemplo simples:

```bash
# 1. Ative o ambiente virtual
source .venv/bin/activate

# 2. Configure suas APIs no .env

# 3. Execute seu primeiro teste
python src/generic_mm_project/main.py "Faça uma análise geral do documento"

# 4. Veja o resultado em output/multimodal_report.md
```

🚀 **Boa sorte com suas análises multimodais!**

---

*Sistema desenvolvido com CrewAI, VoyageAI, OpenAI GPT-4o e Upstash Vector*