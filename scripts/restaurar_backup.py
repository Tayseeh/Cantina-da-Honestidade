"""Restaura backup MySQL criado por backup.py. Requer cliente mysql no PATH."""
from __future__ import annotations
import os,sys,subprocess,json,hashlib,zipfile
from pathlib import Path
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
load_dotenv(BASE / '.env')
def sha(path):
    """Calcula o resumo SHA-256 de um arquivo para conferir sua integridade."""
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def main():
    """Executa a rotina principal do script a partir das configurações do projeto."""
    backup=Path(input("Caminho completo da pasta de backup: ").strip().strip('"')).expanduser().resolve()
    # Lê o manifesto para localizar os arquivos e validar sua integridade antes de restaurar.
    manifest=json.loads((backup/"manifest.json").read_text(encoding="utf-8"))
    sql=backup/manifest["database"]; uploads=backup/manifest["uploads"]
    # Interrompe a restauração se algum arquivo não corresponder ao checksum registrado.
    if sha(sql)!=manifest["database_sha256"] or sha(uploads)!=manifest["uploads_sha256"]:
        raise RuntimeError("Checksum inválido; backup possivelmente incompleto.")
    print("Destino:",os.getenv("CANTINA_DB_HOST","localhost"),os.getenv("CANTINA_DB_NAME","cantina_honestidade"))
    if input("Isso SUBSTITUI os dados do banco MySQL selecionado. Digite RESTAURAR: ").strip()!="RESTAURAR":
        print("Cancelado."); return 0
    env=os.environ.copy(); env["MYSQL_PWD"]=os.getenv("CANTINA_DB_PASSWORD","")
    cmd=["mysql","--host",os.getenv("CANTINA_DB_HOST","localhost"),
         "--port",os.getenv("CANTINA_DB_PORT","3306"),
         "--user",os.getenv("CANTINA_DB_USER","cantina_app"),
         os.getenv("CANTINA_DB_NAME","cantina_honestidade")]
    # Importa o SQL no banco selecionado no .env; essa etapa substitui os dados existentes.
    with sql.open("rb") as f: subprocess.run(cmd,env=env,stdin=f,check=True)
    with zipfile.ZipFile(uploads) as z: z.extractall(BASE)
    print("Restauração concluída.")
    return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print("Falha ao restaurar:",e,file=sys.stderr); raise SystemExit(1)
