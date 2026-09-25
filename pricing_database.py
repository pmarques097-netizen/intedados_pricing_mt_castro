from pathlib import Path
from datetime import datetime
import json, re, time
import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
SQL_DIR = ROOT / "sql"
CACHE_DIR = ROOT / "data" / "banco_cache"
HIST_FILE = CACHE_DIR / "historico_atualizacoes.csv"
DB_FILE = CONFIG_DIR / "database.json"

for _p in (CONFIG_DIR, SQL_DIR, CACHE_DIR):
    _p.mkdir(parents=True, exist_ok=True)

def carregar_config_banco():
    padrao = {"host":"", "port":"5432", "database":"", "user":""}
    try:
        if DB_FILE.exists():
            x=json.loads(DB_FILE.read_text(encoding="utf-8"))
            padrao.update({k:str(x.get(k,"")) for k in padrao})
    except Exception: pass
    return padrao

def salvar_config_banco(cfg):
    # senha não é persistida em arquivo local
    DB_FILE.write_text(json.dumps({k:str(cfg.get(k,"")) for k in ["host","port","database","user"]}, ensure_ascii=False, indent=2), encoding="utf-8")

def ler_sql(nome):
    p=SQL_DIR/nome
    return p.read_text(encoding="utf-8") if p.exists() else ""

def salvar_sql(nome, texto):
    (SQL_DIR/nome).write_text(texto, encoding="utf-8")

def _conectar(cfg, senha):
    """V9.4.1: usa EXCLUSIVAMENTE os valores recebidos da tela."""
    cfg=dict(cfg or {})
    host=str(cfg.get("host","")).strip()
    port=int(str(cfg.get("port","5432")).strip() or "5432")
    database=str(cfg.get("database","")).strip()
    user=str(cfg.get("user","")).strip()
    password=str(senha if senha is not None else "")
    sslmode=str(cfg.get("sslmode","prefer") or "prefer").strip()
    if not host or not database or not user:
        raise RuntimeError("Preencha Host, Banco e Usuário.")
    return psycopg2.connect(
        host=host, port=port, dbname=database, user=user,
        password=password, connect_timeout=8, sslmode=sslmode
    )

def testar_conexao(cfg, senha):
    t=time.time()
    with _conectar(cfg,senha) as con:
        with con.cursor() as cur:
            cur.execute("select current_user, current_database(), inet_server_addr()::text, inet_server_port()")
            row=cur.fetchone()
    return {"ok":True,"segundos":round(time.time()-t,2),
            "usuario":row[0],"banco":row[1],"servidor":row[2],"porta":row[3]}

def sql_venda_competencia(sql, ano, mes):
    """V9.4 — muda somente a fonte. Não recalcula nenhuma regra do Pricing."""
    ini=pd.Timestamp(year=int(ano),month=int(mes),day=1)
    fim=ini+pd.offsets.MonthEnd(1)
    a=ini.strftime("%Y-%m-%d 00:00:00")
    b=fim.strftime("%Y-%m-%d 23:59:59")
    pat=r"me\.datahora\s+BETWEEN\s+'[^']+'\s+AND\s+'[^']+'"
    novo=f"me.datahora BETWEEN '{a}' AND '{b}'"
    if not re.search(pat,sql,flags=re.I):
        raise RuntimeError("Não encontrei o filtro BETWEEN de me.datahora no Venda.sql.")
    return re.sub(pat,novo,sql,count=1,flags=re.I)

def _ultima_atualizacao_ok_hoje(fonte):
    """Retorna True quando a fonte já teve atualização OK hoje."""
    if not HIST_FILE.exists():
        return False
    try:
        h=pd.read_csv(HIST_FILE,dtype=str)
        if h.empty or "Fonte" not in h.columns or "Status" not in h.columns or "Atualizado_em" not in h.columns:
            return False
        x=h[(h["Fonte"].astype(str)==str(fonte)) & (h["Status"].astype(str).str.upper()=="OK")].copy()
        if x.empty:
            return False
        d=pd.to_datetime(x["Atualizado_em"],errors="coerce")
        return bool((d.dt.date==datetime.now().date()).any())
    except Exception:
        return False

def executar_dataframe(cfg, senha, sql):
    con=_conectar(cfg,senha)
    try: return pd.read_sql_query(sql,con)
    finally: con.close()

def _registrar(fonte, competencia, registros, segundos, status, detalhe=""):
    row=pd.DataFrame([{"Atualizado_em":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Fonte":fonte,"Competencia":competencia,"Registros":int(registros),"Tempo_s":round(float(segundos),2),"Status":status,"Detalhe":detalhe}])
    if HIST_FILE.exists():
        try: old=pd.read_csv(HIST_FILE,dtype=str); row=pd.concat([old,row],ignore_index=True)
        except Exception: pass
    row.tail(500).to_csv(HIST_FILE,index=False,encoding="utf-8-sig")

def atualizar_competencia(cfg, senha, ano, mes):
    comp=f"{int(ano):04d}-{int(mes):02d}"
    sql=sql_venda_competencia(ler_sql("venda.sql"),ano,mes)
    t=time.time()
    try:
        df=executar_dataframe(cfg,senha,sql)
        alvo=CACHE_DIR/f"venda_{comp}.parquet"
        tmp=alvo.with_suffix(".tmp.parquet")
        df.to_parquet(tmp,index=False); tmp.replace(alvo)
        _registrar("Venda",comp,len(df),time.time()-t,"OK")
        return len(df),alvo
    except Exception as e:
        _registrar("Venda",comp,0,time.time()-t,"ERRO",str(e)[:300]); raise

def atualizar_fotografia(cfg, senha, nome_sql, nome_saida, uma_vez_ao_dia=False, forcar=False):
    """Atualiza fotografia do banco. Quando diário, reaproveita o cache do mesmo dia."""
    alvo=CACHE_DIR/nome_saida
    if uma_vez_ao_dia and not forcar and alvo.exists() and _ultima_atualizacao_ok_hoje(nome_sql):
        try:
            n=len(pd.read_parquet(alvo))
        except Exception:
            n=0
        _registrar(nome_sql,"ATUAL",n,0,"CACHE_DIA","Já atualizado hoje; cache preservado.")
        return n,alvo
    t=time.time()
    try:
        df=executar_dataframe(cfg,senha,ler_sql(nome_sql))
        tmp=alvo.with_suffix(".tmp.parquet")
        df.to_parquet(tmp,index=False); tmp.replace(alvo)
        _registrar(nome_sql,"ATUAL",len(df),time.time()-t,"OK")
        return len(df),alvo
    except Exception as e:
        _registrar(nome_sql,"ATUAL",0,time.time()-t,"ERRO",str(e)[:300]); raise

def historico():
    try: return pd.read_csv(HIST_FILE) if HIST_FILE.exists() else pd.DataFrame()
    except Exception: return pd.DataFrame()
