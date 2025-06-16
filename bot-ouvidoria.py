import logging
import os
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import google.generativeai as genai

# === Configurações ===
TELEGRAM_TOKEN = "SEU_TELEGRAM_TOKEN"
GEMINI_API_KEY = "SEU_GEMINI_API_KEY"

# O ideal é a criação de um .env que irá receber suas chaves, favor criar e utilizar.

genai.configure(api_key=GEMINI_API_KEY)

# Inicializar modelo Gemini
model = genai.GenerativeModel('gemini-2.0-flash')

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Estados da Conversa ===
CONFIRMA_IDENTIFICACAO, RECEBER_RELATO = range(2)

# === Funções ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_html(
        rf"Olá {user.mention_html()}! 👋"
        "\n\nBem-vindo ao Oráculo Anônimo da UCSal.\n\n"
        "Deseja realizar sua manifestação de forma:\n"
        "1️⃣ Anônima\n2️⃣ Identificada\n\n"
        "Responda com: `1` ou `2`.",
        reply_markup=ForceReply(selective=True),
    )
    return CONFIRMA_IDENTIFICACAO


async def confirma_identificacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    escolha = update.message.text.strip()
    context.user_data['anonimo'] = escolha == "1"

    if escolha not in ["1", "2"]:
        await update.message.reply_text("Por favor, responda com `1` (anônimo) ou `2` (identificado).")
        return CONFIRMA_IDENTIFICACAO

    await update.message.reply_text(
        "Perfeito! ✍️ Por favor, descreva sua manifestação com o máximo de detalhes possíveis."
    )
    return RECEBER_RELATO


async def receber_relato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    relato = update.message.text
    anonimo = context.user_data.get('anonimo', True)

    prompt = f"""
Você é um assistente para uma ouvidoria universitária. Recebe relatos sobre situações de preconceito, discriminação, violência simbólica e outros problemas no ambiente acadêmico.

Analise o relato abaixo e execute duas tarefas:
1. Classifique o tipo de manifestação: (Exemplos: Racismo, LGBTfobia, Assédio, Capacitismo, Outro).
2. Classifique o nível de gravidade: (Baixa, Média, Alta).

Retorne a resposta no seguinte formato:
---
DADOS PARA O BANCO/EXCEL
Tipo de manifestação: [Tipo]
Nível de gravidade: [Gravidade]
Análise: [Análise breve e empática]
---

Relato:
\"\"\"{relato}\"\"\"
"""

    response = model.generate_content(prompt)

    resposta_texto = response.text

    # Mensagem para o usuário
    if anonimo:
        identificacao = "🕵️ Anônimo"
    else:
        identificacao = f"👤 @{update.effective_user.username}" if update.effective_user.username else "👤 Usuário identificado"

    await update.message.reply_text(
        f"✅ Sua manifestação foi registrada!\n\n"
        f"{identificacao}\n\n"
        f"🔎 Resultado da análise automática:\n\n"
        f"{resposta_texto}\n\n"
        f"📢 A equipe da ouvidoria irá avaliar seu caso."
    )

    # Aqui você pode adicionar integração com banco de dados, e-mail ou planilha.

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operação cancelada. Se precisar, envie /start para reiniciar.")
    return ConversationHandler.END


# === Main ===
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONFIRMA_IDENTIFICACAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirma_identificacao)],
            RECEBER_RELATO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_relato)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Bot rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
