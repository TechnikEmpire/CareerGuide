# Setup Guide

## English

### Purpose

This guide explains how to create, activate, and verify the local Python environment for CareerGuide using Conda or Miniconda.

The default environment name used in this repository is:

```text
careerguide
```

### Prerequisites

- Conda, Miniconda, or Anaconda is installed
- You can open a terminal in the repository root
- `requirements.txt` is present in the repository root

### WSL on Windows

Run these commands from the repository root:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Miniconda is installed in a different location, replace:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

with the correct path for your machine.

To activate the environment in later sessions:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Windows PowerShell

Open PowerShell after running `conda init powershell` once, or use Anaconda Prompt if Conda is not available in PowerShell yet.

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### Windows Command Prompt

If you prefer `cmd.exe`, open Anaconda Prompt or a Command Prompt where Conda has already been initialized.

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### macOS Terminal

If Conda is installed but shell activation is not loaded automatically, source Conda first.

```bash
cd /path/to/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```bash
cd /path/to/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Verification

After installation, verify the environment with:

```bash
python --version
python -m pip show fastapi numpy pydantic sqlalchemy uvicorn
python -m pytest backend/tests -q
```

### Running Tests

With the environment active and the terminal opened at the repository root, run:

```bash
python -m pytest backend/tests -q
```

If you want more detailed output:

```bash
python -m pytest backend/tests -v
```

### Running the Backend

Once the environment is active, start the backend with:

```bash
uvicorn backend.app.main:app --reload
```

## Русский

### Назначение

Это руководство объясняет, как создать, активировать и проверить локальное Python-окружение для CareerGuide с помощью Conda или Miniconda.

Имя окружения по умолчанию в этом репозитории:

```text
careerguide
```

### Предварительные требования

- установлен Conda, Miniconda или Anaconda
- вы можете открыть терминал в корне репозитория
- в корне репозитория присутствует `requirements.txt`

### WSL в Windows

Запустите эти команды из корня репозитория:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Если Miniconda установлена в другом месте, замените:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

на корректный путь для вашей машины.

Чтобы активировать окружение в следующих сессиях:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Windows PowerShell

Откройте PowerShell после однократного выполнения `conda init powershell` или используйте Anaconda Prompt, если Conda пока недоступна в PowerShell.

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### Windows Command Prompt

Если вы предпочитаете `cmd.exe`, откройте Anaconda Prompt или Command Prompt, где Conda уже была инициализирована.

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### macOS Terminal

Если Conda установлена, но активация оболочки не подключается автоматически, сначала подключите Conda вручную.

```bash
cd /path/to/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```bash
cd /path/to/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Проверка

После установки проверьте окружение командами:

```bash
python --version
python -m pip show fastapi numpy pydantic sqlalchemy uvicorn
python -m pytest backend/tests -q
```

### Запуск тестов

При активированном окружении и открытом терминале в корне репозитория выполните:

```bash
python -m pytest backend/tests -q
```

Если нужен более подробный вывод:

```bash
python -m pytest backend/tests -v
```

### Запуск backend

После активации окружения backend можно запустить так:

```bash
uvicorn backend.app.main:app --reload
```
