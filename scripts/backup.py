"""Backup do MySQL e dos uploads locais. Requer mysqldump no PATH."""
from __future__ import annotations
import os, sys, subprocess, zipfile, json, hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
load_dotenv(BASE / '.env')
BACKUPS=Path(os.getenv("CANTINA_BACKUP_DIR", str(BASE/"backups"))).resolve()
def main():
    """Executa a rotina principal do script a partir das configurações do projeto."""
    # Cria a pasta de destino e identifica esta execução com data e hora.
    BACKUPS.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    dest=BACKUPS/f"mysql_backup_{stamp}"
    dest.mkdir()
    sql=dest/"cantina_honestidade.sql"
    env=os.environ.copy()
    env["MYSQL_PWD"]=os.getenv("CANTINA_DB_PASSWORD","")
    cmd=["mysqldump","--host",os.getenv("CANTINA_DB_HOST","localhost"),
         "--port",os.getenv("CANTINA_DB_PORT","3306"),
         "--user",os.getenv("CANTINA_DB_USER","cantina_app"),
         "--single-transaction","--routines","--triggers",
         os.getenv("CANTINA_DB_NAME","cantina_honestidade")]
    # Exporta o banco MySQL para um arquivo SQL usando as credenciais do .env.
    with sql.open("wb") as f:
        subprocess.run(cmd,env=env,stdout=f,check=True)
    # Inclui no backup os arquivos enviados e armazenados localmente pela aplicação.
    uploads=BASE/"static"/"uploads"
    archive=dest/"uploads.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        if uploads.exists():
            for file in uploads.rglob("*"):
                if file.is_file() and file.name!=".gitkeep":
                    z.write(file,file.relative_to(BASE))
    def sha(path):
        """Calcula o resumo SHA-256 de um arquivo para conferir sua integridade."""
        h=hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
        return h.hexdigest()
    # Registra hashes SHA-256 para detectar arquivos incompletos ou alterados.
    manifest={"created_at":datetime.now().astimezone().isoformat(),
              "database":sql.name,"database_sha256":sha(sql),
              "uploads":archive.name,"uploads_sha256":sha(archive)}
    (dest/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Backup MySQL concluído:",dest)
    return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print("Falha no backup. Verifique se mysqldump está no PATH e se as credenciais estão corretas:",e,file=sys.stderr)
        raise SystemExit(1)
