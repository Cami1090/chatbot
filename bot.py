
import asyncio, json, logging, os, tempfile, unicodedata

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from excel import construir_excel
from modelo import CIUDAD, CIUDADES, LETRA, NODOS, PAIS, resolver_rutas

logging.basicConfig(level=logging.INFO)

ALIAS = {"Santo Domingo de los Colorados": ["santo domingo"],
         "Puerto Francisco de Orellana (Coca)": ["orellana", "coca"],
         "Nueva Loja": ["lago agrio", "nueva loja"]}


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _buscar(texto):
    t = _norm(texto)
    hallados = []
    for ciudad in CIUDADES:
        for nombre in [ciudad] + ALIAS.get(ciudad, []):
            pos = t.find(_norm(nombre))
            if pos >= 0:
                hallados.append((pos, ciudad))
                break
    return [c for _, c in sorted(hallados)]


def _con_gemini(texto):
    from google import genai
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = ("Extrae origen y destino del mensaje. Ciudades válidas: " + ", ".join(CIUDADES) +
              '. Responde SOLO JSON {"origen": "...", "destino": "..."} usando exactamente esos '
              "nombres, o null si no se puede.\n\nMensaje: " + texto)
    r = cliente.models.generate_content(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt)
    s = r.text.strip().strip("`")
    d = json.loads(s[4:] if s.startswith("json") else s)
    if d.get("origen") in CIUDADES and d.get("destino") in CIUDADES:
        return d["origen"], d["destino"]
    return None, None


def interpretar(texto):
    """Texto libre -> (origen, destino) como ciudades. Con GEMINI_API_KEY usa Gemini; si falla, busca nombres."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            o, d = _con_gemini(texto)
            if o and d:
                return o, d
        except Exception:
            logging.exception("Gemini falló; uso búsqueda simple")
    c = _buscar(texto)
    return (c[0], c[1]) if len(c) >= 2 else (None, None)


def teclado(letras, dato):
    filas = [letras[i:i + 3] for i in range(0, len(letras), 3)]
    return InlineKeyboardMarkup([[InlineKeyboardButton(CIUDAD[l], callback_data=dato(l)) for l in f] for f in filas])


async def responder(mensaje, origen, destino):
    """origen/destino = letras de nodo."""
    rutas = await asyncio.to_thread(resolver_rutas, origen, destino)
    if not rutas:
        await mensaje.reply_text("No encontré rutas entre esas ciudades.")
        return
    texto = f"{CIUDAD[origen]} → {CIUDAD[destino]}\n" + "\n".join(
        f"{i+1}) {' → '.join(CIUDAD[l] for l in r['camino'])} ({r['km']:,} km)" for i, r in enumerate(rutas))
    await mensaje.reply_text(texto)
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, f"Rutas_{PAIS}_tres_alternativas_{origen}_{destino}.xlsx")
        construir_excel(origen, destino, rutas, ruta)
        with open(ruta, "rb") as f:
            await mensaje.reply_document(f)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{PAIS}. Origen:", reply_markup=teclado([l for l, _ in NODOS], lambda l: f"o:{l}"))


async def boton(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tipo, _, dato = q.data.partition(":")
    if tipo == "o":
        await q.edit_message_text(f"Origen: {CIUDAD[dato]}\nDestino:",
                                  reply_markup=teclado([l for l, _ in NODOS if l != dato], lambda l: f"d:{dato}|{l}"))
    elif tipo == "d":
        origen, destino = dato.split("|")
        await q.edit_message_text(f"{CIUDAD[origen]} → {CIUDAD[destino]}")
        await responder(q.message, origen, destino)


async def texto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    o, d = await asyncio.to_thread(interpretar, update.message.text)
    if not o or not d or o == d:
        await update.message.reply_text("Usa /start o escribe: de Santa Elena a Tulcán")
        return
    await responder(update.message, LETRA[o], LETRA[d])


def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto))
    app.run_polling()


if __name__ == "__main__":
    main()