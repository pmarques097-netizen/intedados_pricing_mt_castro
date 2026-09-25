
from pathlib import Path
import csv, io, re, unicodedata
import pandas as pd
import streamlit as st

BASE=Path(__file__).resolve().parent
F_CLIENTES=BASE/"CADASTRO_CLIENTES.csv"
F_CNPJS=BASE/"CADASTRO_CLIENTE_CNPJS.csv"
F_USERS=BASE/"CADASTRO_USUARIOS_CLIENTES.csv"

def _norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def _read(path):
    if not path.exists(): return pd.DataFrame()
    for sep in (";",","):
        try:
            d=pd.read_csv(path,sep=sep,dtype=str,encoding="utf-8-sig").fillna("")
            if len(d.columns)>1:return d
        except Exception:pass
    return pd.DataFrame()

def _write(path,df):
    df.to_csv(path,index=False,sep=";",encoding="utf-8-sig")

def _col(df,*names):
    mp={_norm(c):c for c in df.columns}
    for n in names:
        if _norm(n) in mp:return mp[_norm(n)]
    return None

def _next_id(df,col):
    if not col or df.empty:return "1"
    vals=pd.to_numeric(df[col],errors="coerce").dropna()
    return str(int(vals.max())+1 if not vals.empty else 1)

def _ensure(df,cols):
    for c in cols:
        if c not in df.columns:df[c]=""
    return df

def render_admin(login):
    if str(login).strip().lower()!="paulo":
        st.error("Área restrita.")
        return
    st.markdown("## ⚙️ Administração")
    st.caption("Clientes, CNPJs/Lojas, usuários, permissões e auditoria em um único lugar.")
    clientes=_read(F_CLIENTES); cnpjs=_read(F_CNPJS); users=_read(F_USERS)

    # V9.7.2: respeita as colunas reais já existentes no cadastro legado.
    # Evita criar "cliente_id/cliente/status" duplicados quando o arquivo usa
    # "ClienteID/Cliente/Status".
    idc=_col(clientes,"ClienteID","cliente_id","id_cliente","id")
    nc=_col(clientes,"Cliente","cliente","nome_cliente","nome","razao_social")
    rc=_col(clientes,"Rede Principal","rede_principal","rede","grupo")
    sc=_col(clientes,"Status","status","ativo")
    if not idc:
        clientes["ClienteID"]=""
        idc="ClienteID"
    if not nc:
        clientes["Cliente"]=""
        nc="Cliente"
    if not rc:
        clientes["Rede Principal"]=""
        rc="Rede Principal"
    if not sc:
        clientes["Status"]="ATIVO"
        sc="Status"

    # Remove somente as colunas auxiliares vazias criadas pela V9.7.0/7.1,
    # sem tocar em dados preenchidos.
    _canon={idc,nc,rc,sc}
    for _aux in ["cliente_id","cliente","rede_principal","status"]:
        if _aux in clientes.columns and _aux not in _canon:
            if clientes[_aux].astype(str).str.strip().eq("").all():
                clientes=clientes.drop(columns=[_aux])

    cnpjs=_ensure(cnpjs,["cliente_id","cnpj","loja","codigo_loja","principal","status"])
    users=_ensure(users,["cliente_id","usuario","nome","perfil","status"])

    t1,t2,t3,t4,t5=st.tabs(["🏢 Clientes","🏪 CNPJs / Lojas","👤 Usuários","🔐 Permissões","📋 Auditoria"])

    with t1:
        a,b,c,d=st.columns(4)
        a.metric("Clientes",len(clientes))
        b.metric("CNPJs/Lojas",len(cnpjs))
        c.metric("Usuários",len(users))
        ativos=(clientes[sc].astype(str).str.upper().isin(["ATIVO","SIM","1","TRUE"])).sum() if sc in clientes else len(clientes)
        d.metric("Clientes ativos",int(ativos))
        st.markdown("### Novo cliente")
        with st.form("adm_novo_cliente",clear_on_submit=True):
            nome=st.text_input("Nome do cliente")
            rede=st.text_input("Rede principal")
            status=st.selectbox("Status",["ATIVO","INATIVO"])
            ok=st.form_submit_button("➕ Criar cliente",use_container_width=True)
        if ok:
            if not nome.strip():st.error("Informe o nome do cliente.")
            else:
                row={c:"" for c in clientes.columns}
                row[idc]=_next_id(clientes,idc);row[nc]=nome.strip();row[rc]=rede.strip();row[sc]=status
                clientes=pd.concat([clientes,pd.DataFrame([row])],ignore_index=True)
                _write(F_CLIENTES,clientes);st.success("Cliente criado.");st.rerun()
        st.markdown("### Clientes cadastrados")
        st.dataframe(clientes,use_container_width=True,hide_index=True)

        st.markdown("### ✏️ Alterar dados do cliente")
        if clientes.empty:
            st.info("Nenhum cliente cadastrado para alteração.")
        else:
            _edit_opts={}
            for _ix,_r in clientes.iterrows():
                _cid=str(_r.get(idc,""))
                _rot=f'{_r.get(nc,"") or "Cliente sem nome"} — {_r.get(rc,"") or "Sem rede principal"} — ID {_cid}'
                _edit_opts[_rot]=(_ix,_cid)
            _sel_edit=st.selectbox("Selecione o cliente para editar",list(_edit_opts),key="adm_edit_cliente_sel")
            _ix_edit,_cid_edit=_edit_opts[_sel_edit]
            _r_edit=clientes.loc[_ix_edit]
            with st.form("adm_editar_cliente"):
                _nome_edit=st.text_input("Nome do cliente",value=str(_r_edit.get(nc,"")))
                _rede_edit=st.text_input("Rede principal",value=str(_r_edit.get(rc,"")))
                _status_atual=str(_r_edit.get(sc,"ATIVO")).upper()
                _status_opts=["ATIVO","INATIVO"]
                _status_idx=1 if _status_atual=="INATIVO" else 0
                _status_edit=st.selectbox("Status",_status_opts,index=_status_idx)
                _salvar_edit=st.form_submit_button("💾 Salvar alterações",use_container_width=True)
            if _salvar_edit:
                if not _nome_edit.strip():
                    st.error("Informe o nome do cliente.")
                else:
                    clientes.at[_ix_edit,nc]=_nome_edit.strip()
                    clientes.at[_ix_edit,rc]=_rede_edit.strip()
                    clientes.at[_ix_edit,sc]=_status_edit
                    _write(F_CLIENTES,clientes)
                    st.success("Dados do cliente alterados com sucesso.")
                    st.rerun()

    ids=[]
    if not clientes.empty:
        for _,r in clientes.iterrows():
            ids.append((str(r.get(idc,"")),f'{r.get(nc,"")} — {r.get(rc,"")}'))
    label_to_id={label:i for i,label in ids}

    with t2:
        if not ids:st.info("Cadastre primeiro um cliente.")
        else:
            sel=st.selectbox("Cliente",list(label_to_id),key="adm_cnpj_cliente")
            cid=label_to_id[sel]
            st.markdown("### Adicionar CNPJ / Loja")
            with st.form("adm_add_cnpj",clear_on_submit=True):
                cnpj=st.text_input("CNPJ")
                loja=st.text_input("Nome da loja")
                codigo=st.text_input("Código interno da loja")
                principal=st.checkbox("É a loja/rede principal")
                ok2=st.form_submit_button("➕ Adicionar CNPJ",use_container_width=True)
            if ok2:
                dig=re.sub(r"\D","",cnpj)
                if len(dig)!=14:st.error("Informe um CNPJ com 14 dígitos.")
                else:
                    row={c:"" for c in cnpjs.columns}
                    row["cliente_id"]=cid;row["cnpj"]=dig;row["loja"]=loja.strip()
                    row["codigo_loja"]=codigo.strip();row["principal"]="SIM" if principal else "NÃO";row["status"]="ATIVO"
                    cnpjs=pd.concat([cnpjs,pd.DataFrame([row])],ignore_index=True)
                    _write(F_CNPJS,cnpjs);st.success("CNPJ/Loja adicionado.");st.rerun()
            st.markdown("### Importação em massa")
            arq=st.file_uploader("Excel/CSV com CNPJ, Loja e Código",type=["xlsx","csv"],key="adm_import_cnpj")
            if arq is not None:
                try:
                    imp=pd.read_excel(arq,dtype=str) if arq.name.lower().endswith("xlsx") else pd.read_csv(arq,dtype=str)
                    st.dataframe(imp.head(20),use_container_width=True,hide_index=True)
                    if st.button("📥 Importar para este cliente",key="adm_confirm_import"):
                        imp.columns=[_norm(c) for c in imp.columns]
                        cc=next((c for c in imp.columns if c in ["cnpj","cpf_cnpj"]),None)
                        if not cc:st.error("A planilha precisa ter uma coluna CNPJ.")
                        else:
                            novos=[]
                            for _,rr in imp.iterrows():
                                dig=re.sub(r"\D","",str(rr.get(cc,"")))
                                if len(dig)==14:
                                    novos.append({"cliente_id":cid,"cnpj":dig,
                                      "loja":str(rr.get("loja",rr.get("nome_loja",""))),
                                      "codigo_loja":str(rr.get("codigo_loja",rr.get("codigo",""))),
                                      "principal":str(rr.get("principal","NÃO")),"status":"ATIVO"})
                            cnpjs=pd.concat([cnpjs,pd.DataFrame(novos)],ignore_index=True)
                            cnpjs=cnpjs.drop_duplicates(subset=["cliente_id","cnpj"],keep="last")
                            _write(F_CNPJS,cnpjs);st.success(f"{len(novos)} registros processados.");st.rerun()
                except Exception as e:st.error(f"Não foi possível ler o arquivo: {e}")
            vis=cnpjs[cnpjs["cliente_id"].astype(str).eq(cid)] if "cliente_id" in cnpjs else cnpjs
            st.dataframe(vis,use_container_width=True,hide_index=True)

    with t3:
        if not ids:st.info("Cadastre primeiro um cliente.")
        else:
            selu=st.selectbox("Cliente",list(label_to_id),key="adm_user_cliente"); cid=label_to_id[selu]
            with st.form("adm_add_user",clear_on_submit=True):
                u=st.text_input("Usuário/login");nomeu=st.text_input("Nome")
                perfil=st.selectbox("Perfil",["ADMIN CLIENTE","DIRETORIA","COMPRADOR","GERENTE","VISUALIZAÇÃO"])
                oku=st.form_submit_button("➕ Vincular usuário",use_container_width=True)
            if oku:
                if not u.strip():st.error("Informe o usuário.")
                else:
                    row={c:"" for c in users.columns};row["cliente_id"]=cid;row["usuario"]=u.strip()
                    row["nome"]=nomeu.strip();row["perfil"]=perfil;row["status"]="ATIVO"
                    users=pd.concat([users,pd.DataFrame([row])],ignore_index=True)
                    _write(F_USERS,users);st.success("Usuário vinculado.");st.rerun()
            visu=users[users["cliente_id"].astype(str).eq(cid)] if "cliente_id" in users else users
            st.dataframe(visu,use_container_width=True,hide_index=True)

    with t4:
        st.markdown("### Matriz de acesso")
        st.info("O usuário paulo permanece Master. Os demais usuários ficam limitados ao cliente_id e, portanto, ao grupo de CNPJs vinculado.")
        matriz=pd.DataFrame([
            ["paulo","MASTER","Todos os clientes","Administração + Banco + Pricing"],
            ["ADMIN CLIENTE","Cliente","Grupo de CNPJs do cliente","Cadastros do próprio cliente + Pricing"],
            ["DIRETORIA","Cliente","Grupo de CNPJs do cliente","Visões executivas"],
            ["COMPRADOR","Cliente","Escopo do cliente","Visões de compras/pricing"],
            ["GERENTE","Cliente/Loja","Lojas autorizadas","Visões operacionais"],
            ["VISUALIZAÇÃO","Cliente","Escopo autorizado","Somente leitura"],
        ],columns=["Perfil","Escopo","Dados","Permissão"])
        st.dataframe(matriz,use_container_width=True,hide_index=True)

    with t5:
        st.markdown("### Diagnóstico dos vínculos")
        problemas=[]
        valid=set(clientes[idc].astype(str)) if idc in clientes else set()
        for nome,df in [("CNPJ",cnpjs),("Usuário",users)]:
            if "cliente_id" in df:
                invalid=df[~df["cliente_id"].astype(str).isin(valid) & df["cliente_id"].astype(str).ne("")]
                if not invalid.empty:problemas.append(f"{nome}: {len(invalid)} vínculo(s) sem cliente válido.")
        if problemas:
            for p in problemas:st.warning(p)
        else:st.success("Estrutura de vínculos sem inconsistências detectadas.")
        st.caption("A V9.7 mantém os arquivos legados como fonte para preservar compatibilidade com o Pricing atual.")
