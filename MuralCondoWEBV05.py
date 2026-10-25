import flet as ft
import firebase_admin
from firebase_admin import credentials, firestore
import urllib.parse

# =====================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS (FIREBASE)
# Lembre-se de colar o arquivo 'chave-firebase.json' dentro da pasta:
# C:\Users\Mânica\PycharmProjects\WelcomeScreen\
# =====================================================================
try:
    cred = credentials.Certificate("chave-firebase.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Erro ao conectar ao Firebase (Usando dados simulados): {e}")
    db = None


def main(page: ft.Page):
    page.title = "Mural Desapego Condomínio"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # Componentes Visuais do Formulário de Cadastro
    txt_titulo = ft.TextField(label="O que você está desapegando?", hint_text="Ex: Bicicleta, Sofá, Livro")
    txt_apto = ft.TextField(label="Seu Bloco e Apartamento", hint_text="Ex: Bloco A - Ap 102")
    txt_whatsapp = ft.TextField(label="Seu WhatsApp (com DDD)", hint_text="Ex: 11999998888",
                                keyboard_type=ft.KeyboardType.NUMBER)
    txt_senha = ft.TextField(label="Crie uma senha para apagar o anúncio depois", password=True,
                             can_reveal_password=True, hint_text="Mínimo 4 caracteres")

    dropdown_tipo = ft.Dropdown(
        label="Modalidade",
        options=[ft.dropdown.Option("Doação"), ft.dropdown.Option("Troca"), ft.dropdown.Option("Venda")],
        on_select=lambda e: atualizar_campo_preco()  # Corrigido para on_select
    )
    txt_preco = ft.TextField(label="Preço (R$)", visible=False, value="0")

    # Componentes Visuais para a Janela de Confirmação de Exclusão
    txt_senha_confirmacao = ft.TextField(label="Digite a senha deste anúncio", password=True, can_reveal_password=True)
    id_item_para_excluir = ft.Text(visible=False)
    senha_correta_temporaria = ft.Text(visible=False)

    lista_produtos = ft.ListView(expand=True, spacing=15, padding=10)

    def atualizar_campo_preco():
        txt_preco.visible = (dropdown_tipo.value == "Venda")
        page.update()

    def carregar_itens_do_banco():
        lista_produtos.controls.clear()

        if db:
            docs = db.collection("itens_condominio").order_by("data", direction=firestore.Query.DESCENDING).stream()
            itens = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        else:
            itens = [
                {"id": "1", "titulo": "Bicicleta Infantil", "tipo": "Doação", "preco": "0", "apto": "Bl 2 - Ap 402",
                 "whatsapp": "11999998888", "senha": "1234"},
                {"id": "2", "titulo": "Furadeira Bosch", "tipo": "Troca", "preco": "0", "apto": "Bl 1 - Ap 105",
                 "whatsapp": "11999998888", "senha": "1234"},
            ]

        for item in itens:
            # Corrigido para ft.Colors (C maiúsculo)
            cor_fundo = ft.Colors.GREEN_100 if item["tipo"] == "Doação" else ft.Colors.BLUE_100 if item[
                                                                                                       "tipo"] == "Troca" else ft.Colors.ORANGE_100
            detalhe_tipo = item["tipo"] if item["tipo"] != "Venda" else f"Venda - R$ {item['preco']}"

            wpp_limpo = "".join(filter(str.isdigit, item.get("whatsapp", "")))
            mensagem_texto = f"Olá! Vi seu anúncio da '{item['titulo']}' ({item['tipo']}) no Mural do Condomínio e tenho interesse."
            link_whatsapp = f"https://wa.me/{wpp_limpo}?text={urllib.parse.quote(mensagem_texto)}"

            def criar_evento_excluir(id_doc, senha_doc):
                return lambda e: abrir_modal_exclusao(id_doc, senha_doc)

            lista_produtos.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(item["titulo"], weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLACK),
                            ft.Text(f"Modalidade: {detalhe_tipo}", size=14, color=ft.Colors.GREY_900),
                            ft.Text(f"Retirar em: {item['apto']}", color=ft.Colors.GREY_700, size=12),
                        ], expand=True),

                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.SMS_OUTLINED,  # Corrigido para o padrão atual
                                icon_color=ft.Colors.GREEN_700,
                                icon_size=26,
                                tooltip="Chamar no WhatsApp",
                                url=link_whatsapp
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_ROUNDED,  # Corrigido nomenclatura inexistente
                                icon_color=ft.Colors.RED_600,
                                icon_size=26,
                                tooltip="Remover anúncio",
                                on_click=criar_evento_excluir(item["id"], item.get("senha", ""))
                            ),
                        ], spacing=5)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=cor_fundo,
                    padding=15,
                    border_radius=10,
                )
            )
        page.update()

    def salvar_novo_anuncio(e):
        if not txt_titulo.value or not txt_apto.value or not dropdown_tipo.value or not txt_whatsapp.value or not txt_senha.value:
            mostrar_mensagem("Por favor, preencha todos os campos obrigatórios!")
            return

        if len(txt_senha.value) < 4:
            mostrar_mensagem("A senha de exclusão deve ter pelo menos 4 caracteres!")
            return

        novo_item = {
            "titulo": txt_titulo.value,
            "tipo": dropdown_tipo.value,
            "preco": txt_preco.value if dropdown_tipo.value == "Venda" else "0",
            "apto": txt_apto.value,
            "whatsapp": txt_whatsapp.value,
            "senha": txt_senha.value,
            "data": firestore.SERVER_TIMESTAMP if db else None
        }

        if db:
            db.collection("itens_condominio").add(novo_item)

        txt_titulo.value = ""
        txt_apto.value = ""
        txt_whatsapp.value = ""
        txt_senha.value = ""
        dropdown_tipo.value = None
        txt_preco.visible = False
        dialog_cadastro.open = False

        carregar_itens_do_banco()
        mostrar_mensagem("Anúncio publicado com sucesso!")

    def abrir_modal_exclusao(id_doc, senha_doc):
        id_item_para_excluir.value = id_doc
        senha_correta_temporaria.value = senha_doc
        txt_senha_confirmacao.value = ""
        page.dialog = dialog_exclusao
        dialog_exclusao.open = True
        page.update()

    def confirmar_e_deletar(e):
        id_alvo = id_item_para_excluir.value
        senha_digitada = txt_senha_confirmacao.value

        if db:
            doc_ref = db.collection("itens_condominio").document(id_alvo)
            doc = doc_ref.get()

            if doc.exists and doc.to_dict().get("senha") == senha_digitada:
                doc_ref.delete()
                dialog_exclusao.open = False
                carregar_itens_do_banco()
                mostrar_mensagem("Anúncio removido com sucesso!")
            else:
                mostrar_mensagem("Senha incorreta! Não foi possível remover.")
        else:
            if senha_correta_temporaria.value == senha_digitada:
                dialog_exclusao.open = False
                mostrar_mensagem("Sucesso! (Simulação: Item excluído)")
            else:
                mostrar_mensagem("Senha incorreta!")

    def mostrar_mensagem(texto):
        page.snack_bar = ft.SnackBar(ft.Text(texto))
        page.snack_bar.open = True
        page.update()

        # Modais Atualizados e Limpos de Erros

    dialog_cadastro = ft.AlertDialog(
        title=ft.Text("Anunciar Novo Item"),
        content=ft.Column([txt_titulo, txt_apto, txt_whatsapp, dropdown_tipo, txt_preco, txt_senha], tight=True,
                          spacing=10),
        actions=[
            # Botão de Cancelar corrigido sem o 'variant'
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_cadastro, "open", False) or page.update()),
            ft.Button("Publicar", on_click=salvar_novo_anuncio, bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE)
        ],
    )

    dialog_exclusao = ft.AlertDialog(
        title=ft.Text("Excluir Anúncio"),
        content=ft.Column([
            ft.Text("Este item já foi vendido ou doado? Digite a senha cadastrada para tirá-lo do mural."),
            txt_senha_confirmacao
        ], tight=True, spacing=10),
        actions=[
            # Botão de Voltar corrigido sem o 'variant'
            ft.TextButton("Voltar", on_click=lambda e: setattr(dialog_exclusao, "open", False) or page.update()),
            ft.Button("Confirmar Exclusão", on_click=confirmar_e_deletar, bgcolor=ft.Colors.RED_600,
                      color=ft.Colors.WHITE)
        ],
    )

    page.app_bar = ft.AppBar(
        title=ft.Text("Mural Virtual do Condomínio", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.TEAL,
        center_title=True,
    )

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        bgcolor=ft.Colors.TEAL,
        on_click=lambda e: setattr(dialog_cadastro, "open", True) or page.update()
    )

    page.add(lista_produtos)
    carregar_itens_do_banco()


if __name__ == "__main__":
    # Corrigido de ft.app para ft.run conforme as novas diretrizes do framework
    ft.run(main, view=ft.AppView.WEB_BROWSER) #  Passe a função 'main' direto!)
