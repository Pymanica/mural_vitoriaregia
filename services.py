import urllib.parse
from firebase_admin import firestore


def carregar_itens_do_banco(db):
    if db:
        docs = db.collection("itens_condominio").order_by(
            "data", direction=firestore.Query.DESCENDING
        ).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    return []


def salvar_novo_anuncio(db, titulo, apto, whatsapp, senha, tipo, preco):
    if not titulo or not apto or not tipo or not whatsapp or not senha:
        return False, "Preencha todos os campos obrigatórios."

    if len(senha) < 4:
        return False, "A senha de exclusão deve ter pelo menos 4 caracteres."

    novo_item = {
        "titulo": titulo,
        "tipo": tipo,
        "preco": preco if tipo == "Venda" else "0",
        "apto": apto,
        "whatsapp": whatsapp,
        "senha": senha,
        "data": firestore.SERVER_TIMESTAMP if db else None,
    }

    try:
        if db:
            db.collection("itens_condominio").add(novo_item)
        return True, "Anúncio publicado com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar anúncio: {e}"


def excluir_anuncio(db, id_doc, senha_digitada):
    try:
        if db:
            doc_ref = db.collection("itens_condominio").document(id_doc)
            doc = doc_ref.get()

            if doc.exists and doc.to_dict().get("senha") == senha_digitada:
                doc_ref.delete()
                return True, "Anúncio removido com sucesso!"

            return False, "Senha incorreta! Não foi possível remover."

        return False, "Modo sem banco de dados."

    except Exception as e:
        return False, f"Erro ao excluir anúncio: {e}"


def montar_link_whatsapp(titulo, tipo, whatsapp):
    wpp_limpo = "".join(filter(str.isdigit, whatsapp))
    mensagem_texto = (
        f"Olá! Vi seu anúncio da '{titulo}' ({tipo}) no Mural do Condomínio e tenho interesse."
    )
    return f"https://wa.me/{wpp_limpo}?text={urllib.parse.quote(mensagem_texto)}"