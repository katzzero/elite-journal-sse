#!/usr/bin/env python3
"""
Script de instalação automática das dependências
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário!")
        print(f"   Versão atual: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")


def install_dependencies():
    """Instala as dependências do requirements.txt"""
    print("\n📦 Instalando dependências...")
    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
            "--upgrade"
        ])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def find_journal_path():
    """Tenta encontrar automaticamente a pasta de journals"""
    print("\n🔍 Procurando pasta de journals do Elite Dangerous...")
    
    if sys.platform == "win32":
        journal_path = Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
    else:
        # Linux/Proton
        journal_path = Path.home() / ".steam" / "steam" / "steamapps" / "compatdata" / "359320" / "pfx" / "drive_c" / "users" / "steamuser" / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
    
    if journal_path.exists():
        print(f"✅ Pasta encontrada: {journal_path}")
        return journal_path
    else:
        print(f"⚠️  Pasta padrão não encontrada: {journal_path}")
        print("   Você pode configurar manualmente via variável de ambiente ELITE_JOURNAL_PATH")
        return None


def create_start_script():
    """Cria scripts de inicialização convenientes"""
    print("\n📝 Criando scripts de inicialização...")
    
    if sys.platform == "win32":
        # Windows batch script
        script_content = """@echo off
echo ====================================
echo Elite Dangerous SSE Server
echo ====================================
echo.
python server.py
pause
"""
        script_path = Path("start_server.bat")
        script_path.write_text(script_content)
        print(f"✅ Criado: {script_path}")
    else:
        # Linux/Mac bash script
        script_content = """#!/bin/bash
echo "===================================="
echo "Elite Dangerous SSE Server"
echo "===================================="
echo ""
python3 server.py
"""
        script_path = Path("start_server.sh")
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        print(f"✅ Criado: {script_path}")


def main():
    print("="*60)
    print("🚀 Elite Dangerous SSE Server - Setup")
    print("="*60)
    
    # Verifica versão do Python
    check_python_version()
    
    # Instala dependências
    if not install_dependencies():
        print("\n❌ Instalação falhou!")
        sys.exit(1)
    
    # Procura pasta de journals
    journal_path = find_journal_path()
    
    # Cria scripts de inicialização
    create_start_script()
    
    print("\n" + "="*60)
    print("✅ Setup concluído com sucesso!")
    print("="*60)
    print("\n📖 Como usar:")
    
    if sys.platform == "win32":
        print("   1. Execute: start_server.bat")
    else:
        print("   1. Execute: ./start_server.sh")
        print("      ou: python3 server.py")
    
    print("   2. Abra o navegador em: http://localhost:8000")
    print("   3. Para acessar de outros dispositivos na rede:")
    print("      http://<seu-ip-local>:8000")
    
    if journal_path:
        print(f"\n📂 Monitorando: {journal_path}")
    else:
        print("\n⚠️  Configure a pasta de journals:")
        print("   set ELITE_JOURNAL_PATH=C:\\Caminho\\Para\\Journals (Windows)")
        print("   export ELITE_JOURNAL_PATH=/caminho/para/journals (Linux/Mac)")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
