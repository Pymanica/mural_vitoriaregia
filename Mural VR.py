import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import urllib.parse
import json

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Mural Desapego Condomínio Vitoria Regia",
    page_icon="🏢",
    layout="centered"
)

# Inicialização segura do Firebase Firestore
@st.cache_resource
def inicializar_firebase():
    try:
        # Se você estiver usando os "Secrets" do Streamlit para não subir o JSON no GitHub:
        if "firebase" in st.secrets:
            firebase_info = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_info)
        else:
            # Caso contrário, tenta ler o arquivo localmente
            cred = credentials.Certificate("chave-firebase.json")
            
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.warning(f"Usando dados simulados (Não foi possível conectar ao Firebase: {e})")
        return None

db = inicializar_firebase()

# Título Principal da Aplicação
st.title("🏢 Mural Desapego Condomínio Vitoria Regia")
st.markdown("---")

# --- ÁREA DE CADASTRO (Criando um formulário em formato Expander) ---
with st.expander("➕ Publicar Novo Anúncio", expanded=False):
    with st.form("form_cadastro", clear_on_submit=True):
        txt_titulo = st.text_input("O que você está desapegando?", placeholder="Ex: Bicicleta, Sofá, Livro")
        txt_apto = st.text_input("Seu Bloco e Apartamento", placeholder="Ex: Bloco A - Ap 102")
        txt_whatsapp = st.text_input("Seu WhatsApp (com DDD apenas números)", placeholder="Ex: 11999998888")
        txt_senha = st.text_input("Crie uma senha para apagar o anúncio depois", type="password", help="Mínimo 4 caracteres")
        
        dropdown_tipo = st.selectbox("Modalidade", ["Doação", "Troca", "Venda"])
        
        # Lógica dinâmica para preço
        txt_preco = 0.0
        if dropdown_tipo == "Venda":
            txt_preco = st.number_input("Preço (R\$)", min_value=0.0, step=10.0, value=0.0)

        botao_enviar = st.form_submit_button("Publicar Anúncio")

        if botao_enviar:
            if not txt_titulo or not txt_apto or not txt_whatsapp or not txt_senha:
                st.error("Por favor, preencha todos os campos obrigatórios!")
            elif len(txt_senha) < 4:
                st.error("A senha de exclusão deve ter pelo menos 4 caracteres!")
            else:
                novo_item = {
                    "titulo": txt_titulo,
                    "tipo": dropdown_tipo,
                    "preco": str(txt_preco) if dropdown_tipo == "Venda" else "0",
                    "apto": txt_apto,
                    "whatsapp": txt_whatsapp,
                    "senha": txt_senha,
                    "data": firestore.SERVER_TIMESTAMP if db else None
                }
                
                if db:
                    db.collection("itens_condominio").add(novo_item)
                    st.success("Anúncio publicado com sucesso!")
                    st.rerun()
                else:
                    st.info("Sucesso! (Modo Simulação: Item processado localmente)")

# --- BUSCA DOS DADOS ---
if db:
    try:
        docs = db.collection("itens_condominio").order_by("data", direction=firestore.Query.DESCENDING).stream()
        itens = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception:
        itens = []
else:
    # Dados simulados idênticos ao seu código Flet original
    itens = [
        {"id": "1", "titulo": "Bicicleta Infantil", "tipo": "Doação", "preco": "0", "apto": "Bl 2 - Ap 402", "whatsapp": "11999998888", "senha": "1234"},
        {"id": "2", "titulo": "Furadeira Bosch", "tipo": "Troca", "preco": "0", "apto": "Bl 1 - Ap 105", "whatsapp": "11999998888", "senha": "1234"},
    ]

# --- EXIBIÇÃO DOS PRODUTOS (Mural) ---
st.subheader("🛒 Itens Disponíveis")

if not itens:
    st.write("Nenhum anúncio ativo no momento.")

for item in itens:
    # Definição visual baseada na modalidade
    detalhe_tipo = item["tipo"] if item["tipo"] != "Venda" else f"Venda - R\$ {item['preco']}"
    
    wpp_limpo = "".join(filter(str.isdigit, item.get("whatsapp", "")))
    mensagem_texto = f"Olá! Vi seu anúncio da '{item['titulo']}' ({item['tipo']}) no Mural do Condomínio e tenho interesse."
    link_whatsapp = f"https://wa.me{wpp_limpo}?text={urllib.parse.quote(mensagem_texto)}"
    
    # Criando os blocos visuais de anúncios usando os Containers nativos do Streamlit
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### **{item['titulo']}**")
            st.markdown(f"**Modalidade:** `{detalhe_tipo}`")
            st.markdown(f"📍 *Retirar em: {item['apto']}*")
            
        with col2:
            st.write("") # Espaçador visual
            # Botão direcionando para o link de WhatsApp
            st.link_button("💬 WhatsApp", link_whatsapp, use_container_width=True)
            
            # Modal de exclusão simplificado via botão com popover (evita trocar de página)
            with st.popover("🗑️ Remover", use_container_width=True):
                st.write("Digite a senha para excluir:")
                senha_confirmacao = st.text_input("Senha", type="password", key=f"senha_{item['id']}")
                botao_deletar = st.button("Confirmar Exclusão", key=f"btn_{item['id']}")
                
                if botao_deletar:
                    if db:
                        doc_ref = db.collection("itens_condominio").document(item["id"])
                        doc = doc_ref.get()
                        if doc.exists and doc.to_dict().get("senha") == senha_confirmacao:
                            doc_ref.delete()
                            st.toast("Anúncio removido com sucesso!")
                            st.rerun()
                        else:
                            st.error("Senha incorreta!")
                    else:
                        if item.get("senha") == senha_confirmacao:
                            st.toast("Sucesso! (Simulação: Item excluído)")
                        else:
                            st.error("Senha incorreta!")
