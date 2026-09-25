from pathlib import Path
import json, os, base64
CFG_FILE=Path(__file__).resolve().parent/"data"/"config_banco_paulo.json"
def _enc(s):
    if os.name!="nt": return ""
    try:
        import win32crypt
        return base64.b64encode(win32crypt.CryptProtectData(str(s).encode(),None,None,None,None,0)).decode()
    except Exception:return ""
def _dec(s):
    if os.name!="nt" or not s:return ""
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(base64.b64decode(s),None,None,None,0)[1].decode()
    except Exception:return ""
def salvar(cfg,senha):
    CFG_FILE.parent.mkdir(parents=True,exist_ok=True)
    e=_enc(senha)
    d={k:cfg.get(k) for k in ("host","port","database","user","sslmode")}
    d["password_dpapi"]=e
    CFG_FILE.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    return bool(e)
def carregar():
    try:
        d=json.loads(CFG_FILE.read_text(encoding="utf-8"))
        return d,_dec(d.get("password_dpapi",""))
    except Exception:return {},""
