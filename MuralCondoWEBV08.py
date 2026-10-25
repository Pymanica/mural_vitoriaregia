import streamlit as st
from firebase_config import init_firebase
from services import (
    carregar_itens_do_banco,
    salvar_novo_anuncio,
    excluir_anuncio,
    montar_link_whatsapp,
)

db = init_firebase()

st.set_page_config(
    page_title="Mural Desapego Condomínio",
    layout="wide"
)

st.title("Mural Virtual do Condomínio")
st.caption("Anuncie itens para doação, troca ou venda dentro do condomínio.")

if "mostrar_form" not in st.session_state:
    st.session_state.mostrar_form = False

if "item_excluir_id" not in st.session_state:
    st.session_state.item_excluir_id = None

if "item_excluir_titulo" not in st.session_state:
    st.session_state.item_excluir_titulo = None

if "item_excluir_senha" not in st.session_state:
    st.session_state.item_excluir_senha = None


col1, col2 = st.columns([1, 4])

with col1:
    if st.button("+ Novo anúncio"):
        st.session_state.mostrar_form = True

with col2:
    st.write("Use o botão acima para cadastrar um novo item.")


if st.session_state.mostrar_form:
    with st.form("form_anuncio"):
        st.subheader("Anunciar Novo Item")

        titulo = st.text_input("O que você está desapegando?", placeholder="Ex: Bicicleta, Sofá, Livro")
        apto = st.text_input("Seu Bloco e Apartamento", placeholder="Ex: Bloco A - Ap 102")
        whatsapp = st.text_input("Seu WhatsApp (com DDD)", placeholder="Ex: 11999998888")
        tipo = st.selectbox("Modalidade", ["Selecione...", "Doação", "Troca", "Venda"])

        preco = "0"
        if tipo == "Venda":
            preco = st.text_input("Preço (R$)", value="0")

        senha = st.text_input("Crie uma senha para apagar o anúncio depois", type="password")
        submitted = st.form_submit_button("Publicar")

        if submitted:
            if tipo == "Selecione...":
                st.error("Selecione a modalidade.")
            else:
                ok, msg = salvar_novo_anuncio(db, titulo, apto, whatsapp, senha, tipo, preco)
                if ok:
                    st.success(msg)
                    st.session_state.mostrar_form = False
                    st.rerun()
                else:
                    st.error(msg)

    if st.button("Cancelar cadastro"):
        st.session_state.mostrar_form = False
        st.rerun()


st.subheader("Itens anunciados")
itens = carregar_itens_do_banco(db)

if not itens:
    st.info("Ainda não há anúncios cadastrados.")
else:
    for item in itens:
        tipo = item.get("tipo", "")
        titulo = item.get("titulo", "")
        apto = item.get("apto", "")
        whatsapp = item.get("whatsapp", "")
        preco = item.get("preco", "0")
        item_id = item.get("id", "")
        senha_item = item.get("senha", "")

        if tipo == "Doação":
            cor_label = "🟢"
            detalhe_tipo = "Doação"
        elif tipo == "Troca":
            cor_label = "🔵"
            detalhe_tipo = "Troca"
        else:
            cor_label = "🟠"
            detalhe_tipo = f"Venda - R$ {preco}"

        link_whatsapp = montar_link_whatsapp(titulo, tipo, whatsapp)

        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 2, 2])

            with c1:
                st.markdown(f"### {cor_label} {titulo}")
                st.write(f"**Modalidade:** {detalhe_tipo}")
                st.write(f"**Retirar em:** {apto}")

            with c2:
                st.link_button("Chamar no WhatsApp", link_whatsapp)

            with c3:
                if st.button("Remover anúncio", key=f"remover_{item_id}"):
                    st.session_state.item_excluir_id = item_id
                    st.session_state.item_excluir_titulo = titulo
                    st.session_state.item_excluir_senha = senha_item


if st.session_state.item_excluir_id:
    st.divider()
    st.subheader("Excluir anúncio")

    st.warning(f"Você está tentando excluir: **{st.session_state.item_excluir_titulo}**")

    senha_digitada = st.text_input("Digite a senha deste anúncio", type="password", key="senha_exclusao")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Confirmar exclusão"):
            ok, msg = excluir_anuncio(db, st.session_state.item_excluir_id, senha_digitada)
            if ok:
                st.success(msg)
                st.session_state.item_excluir_id = None
                st.session_state.item_excluir_titulo = None
                st.session_state.item_excluir_senha = None
                st.rerun()
            else:
                st.error(msg)

    with col2:
        if st.button("Cancelar exclusão"):
            st.session_state.item_excluir_id = None
            st.session_state.item_excluir_titulo = None
            st.session_state.item_excluir_senha = None
            st.rerun()
