import base64, html, io, os, re, time, zipfile
from contextlib import contextmanager

import httpx
import streamlit as st
from PIL import Image
from sarvamai import SarvamAI

st.set_page_config(page_title="Chitthi", layout="wide")

# ---------- Retro pink "desktop" theme ----------
INK, PINK, CREAM, BG = "#4a2e35", "#eba3b8", "#f8f1f1", "#f4cfd3"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700&family=Noto+Serif:wght@400;600&display=swap');
#MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{ visibility: hidden; }}
[data-testid="stExpandSidebarButton"] {{ background: {CREAM}; border: 2px solid {INK}; border-radius: 6px; }}
header[data-testid="stHeader"] {{ background: {PINK}; border-bottom: 3px solid {INK}; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {{ background: {CREAM} !important; color: {INK} !important; }}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{ background: {PINK} !important; }}
.stApp {{
  background-color: {BG};
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400'%3E%3Cpath d='M-50 300 Q150 100 350 250 T750 150' fill='none' stroke='white' stroke-width='2' stroke-dasharray='10 10' opacity='.7'/%3E%3Cpath d='M-50 50 Q250 200 400 60 T700 380' fill='none' stroke='white' stroke-width='2' stroke-dasharray='10 10' opacity='.5'/%3E%3C/svg%3E");
  font-family: 'Montserrat', sans-serif; color: {INK};
}}
h1, h2, h3, p, label, span, div {{ color: {INK}; }}
[data-testid="stSidebar"] {{ background: #f7dde1; border-right: 3px solid {INK}; }}

/* every st.container(key="win_...") becomes a retro window */
[class*="st-key-win"] {{
  background: {CREAM}; border: 3px solid {INK}; border-radius: 10px;
  box-shadow: 6px 6px 0 {INK}; padding: 0 1.2rem 1.2rem; overflow: hidden;
  animation: pop .35s ease-out;
}}
@keyframes pop {{ from {{ transform: translateY(12px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
.titlebar {{
  background: {PINK}; border-bottom: 3px solid {INK}; margin: 0 -1.2rem .8rem;
  padding: .35rem 1rem; display: flex; justify-content: space-between;
  font-weight: 700; letter-spacing: .5px;
}}
.titlebar .ctl {{ letter-spacing: 8px; font-weight: 700; }}

/* chunky retro buttons */
.stButton button, .stDownloadButton button {{
  background: {CREAM}; color: {INK}; border: 3px solid {INK}; border-radius: 8px;
  box-shadow: 3px 3px 0 {INK}; font-weight: 700; transition: all .12s;
}}
.stButton button:hover, .stDownloadButton button:hover {{
  background: {PINK}; color: {INK}; border-color: {INK}; transform: translate(-1px,-1px); box-shadow: 4px 4px 0 {INK};
}}
.stButton button:active {{ transform: translate(3px,3px); box-shadow: none; }}

/* tabs look like taskbar buttons */
.stTabs [data-baseweb="tab-list"] {{ gap: .6rem; }}
.stTabs [data-baseweb="tab"] {{
  background: {CREAM}; border: 3px solid {INK}; border-radius: 8px 8px 0 0; padding: .4rem 1rem; font-weight: 700;
}}
.stTabs [aria-selected="true"] {{ background: {PINK}; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

textarea, [data-baseweb="select"] > div, input {{ border: 2px solid {INK} !important; background: white !important; }}

.letter {{
  background: #fffaf3 repeating-linear-gradient(transparent, transparent 2.35rem, #f0d9dc 2.4rem);
  border: 3px solid {INK}; border-radius: 6px; box-shadow: 5px 5px 0 {INK};
  padding: 1.6rem 2.2rem; font-family: 'Noto Serif', Georgia, serif; font-size: 1.35rem;
  line-height: 2.4rem; white-space: pre-wrap; margin: .5rem 0 1rem;
}}
.hero {{ text-align: center; }}
.hero h1 {{ font-size: 3rem; margin: .2rem 0 0; }}
.hero p {{ font-size: 1.15rem; }}
.step {{ text-align: center; font-weight: 600; }}
.step svg {{ display: block; margin: 0 auto .4rem; }}
.loadbar {{ border: 3px solid {INK}; border-radius: 20px; height: 26px; padding: 3px; background: white; overflow: hidden; }}
.loadbar div {{ height: 100%; width: 0; border-radius: 12px;
  background: repeating-linear-gradient(90deg, {PINK} 0 18px, transparent 18px 24px);
  animation: load 1.8s ease-out forwards; }}
@keyframes load {{ to {{ width: 100%; }} }}
.wait {{ display: flex; align-items: center; gap: .8rem; font-weight: 700; margin: .6rem 0; }}
.wait svg {{ animation: spin 1.2s linear infinite; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* soft animations */
@keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
@keyframes fade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes beat {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.08); }} }}
@keyframes glow {{ 0%,100% {{ box-shadow: 0 0 4px #4cd17a; }} 50% {{ box-shadow: 0 0 10px #4cd17a; }} }}
.hero svg {{ animation: float 4s ease-in-out infinite; }}
.step svg {{ transition: transform .35s ease; }}
.step:hover svg {{ transform: translateY(-4px) rotate(-3deg); }}
[class*="st-key-win"] {{ transition: transform .3s ease, box-shadow .3s ease; }}
[class*="st-key-win"]:hover {{ transform: translate(-2px,-2px); box-shadow: 8px 8px 0 {INK}; }}
.letter, .wait, .stAlert, [data-testid="stAudio"], [data-testid="stImage"] {{ animation: fade .6s ease-out; }}
.stTabs [data-baseweb="tab"] {{ transition: background .25s ease, transform .25s ease; }}
.stTabs [data-baseweb="tab"]:hover {{ transform: translateY(-2px); }}
.stTabs [data-baseweb="tab-panel"] {{ animation: fade .45s ease-out; }}
textarea, input {{ transition: box-shadow .25s ease; }}
textarea:focus, input:focus {{ box-shadow: 0 0 0 3px {PINK} !important; }}
.led {{ transition: background .4s ease; }}
.led.on {{ animation: glow 2.4s ease-in-out infinite; }}
.loadbar div {{ transition: width .8s ease; }}
.footer {{ text-align: center; margin: 70vh 0 1rem; padding-top: 1rem; border-top: 2px dashed {INK}; animation: fade 1s ease-out; }}
.footer p {{ margin: .2rem 0; font-weight: 600; }}
.footer svg {{ animation: beat 1.8s ease-in-out infinite; vertical-align: middle; margin: 0 .3rem; }}
.api {{ display: flex; align-items: center; gap: .5rem; margin: .2rem 0; font-weight: 600; }}
.led {{ width: 12px; height: 12px; border-radius: 50%; border: 2px solid {INK}; background: #c9c0c2; }}
.led.on {{ background: #4cd17a; box-shadow: 0 0 6px #4cd17a; }}
</style>""", unsafe_allow_html=True)

S = f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"'
ICONS = {
    "envelope": f'<svg viewBox="0 0 120 80" width="{{w}}"><rect x="4" y="4" width="112" height="72" fill="{CREAM}" {S}/><path d="M4 4 L60 46 L116 4 M4 76 L48 37 M116 76 L72 37" fill="none" {S}/></svg>',
    "open": f'<svg viewBox="0 0 120 120" width="{{w}}"><rect x="28" y="4" width="64" height="70" fill="{CREAM}" {S}/><path d="M38 20h44M38 32h44M38 44h30" {S}/><path d="M4 52 L60 92 L116 52 V116 H4 Z" fill="{PINK}" {S}/><path d="M4 116 L60 76 L116 116" fill="none" {S}/></svg>',
    "heart": f'<svg viewBox="0 0 100 110" width="{{w}}"><path d="M10 6h80a6 6 0 0 1 6 6v64a6 6 0 0 1-6 6H62l-12 20-12-20H10a6 6 0 0 1-6-6V12a6 6 0 0 1 6-6z" fill="{CREAM}" {S}/><path d="M50 70 C20 50 22 24 38 24 C46 24 50 32 50 32 C50 32 54 24 62 24 C78 24 80 50 50 70Z" fill="#e2664a" {S}/></svg>',
    "hourglass": f'<svg viewBox="0 0 80 110" width="{{w}}"><path d="M8 6h64M8 104h64" {S} stroke-width="8"/><path d="M16 10 C16 40 40 45 40 55 C40 65 16 70 16 100 H64 C64 70 40 65 40 55 C40 45 64 40 64 10Z" fill="{CREAM}" {S}/><path d="M28 92 L40 74 L52 92Z" fill="{INK}"/></svg>',
    "folder": f'<svg viewBox="0 0 120 90" width="{{w}}"><path d="M6 10h34l8 8h50v66H6Z" fill="{CREAM}" {S}/><path d="M6 84 L20 34 H114 L98 84Z" fill="{PINK}" {S}/></svg>',
}


def icon(name, w=70):
    return ICONS[name].replace("{w}", str(w))


def titlebar(text):
    st.markdown(f"<div class='titlebar'><span>{text}</span><span class='ctl'>_ □ ✕</span></div>",
                unsafe_allow_html=True)


@contextmanager
def waiting(msg):
    """Like st.spinner, but with a spinning hourglass."""
    ph = st.empty()
    ph.markdown(f"<div class='wait'>{icon('hourglass', 34)}<span>{html.escape(msg)}</span></div>",
                unsafe_allow_html=True)
    try:
        yield
    finally:
        ph.empty()


def footer():
    st.markdown(f"<div class='footer'><p>Made with {icon('heart', 26)} by Pratik and Lalmuankima</p>"
                "<p>Made using Sarvam API, for Sarvam</p></div>", unsafe_allow_html=True)


def letter(text):
    st.markdown(f"<div class='letter'>{html.escape(text)}</div>", unsafe_allow_html=True)


GP_LANGS = {"Hindi": "hi-IN", "Gujarati": "gu-IN", "Bengali": "bn-IN", "Marathi": "mr-IN",
            "Tamil": "ta-IN", "Telugu": "te-IN", "Kannada": "kn-IN", "Malayalam": "ml-IN",
            "Punjabi": "pa-IN", "Odia": "od-IN"}
KID_LANGS = {"English": "en-IN", "Hindi": "hi-IN"}
APIS = ["Sarvam Vision", "Sarvam Translate", "Sarvam-105B", "Saaras STT", "Bulbul TTS", "Voice Cloning"]

st.session_state.setdefault("used", set())
st.session_state.setdefault("gp_name", "Hindi")
st.session_state.setdefault("kid_name", "English")


def mark(api):
    st.session_state.used.add(api)


# ---------- Onboarding (first screen) ----------
def start(key_in):
    # copy welcome-screen picks into the sidebar widgets' keys
    st.session_state.gp_name = st.session_state.w_gp
    st.session_state.kid_name = st.session_state.w_kid
    if key_in:
        st.session_state.api_key = key_in
    st.session_state.started = True


if not st.session_state.get("started"):
    st.markdown("<div class='hero'>" + icon("open", 110) +
                "<h1>Chitthi</h1><p><i>Families live in different scripts. "
                "Chitthi carries the letter across.</i></p></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid, st.container(key="win_welcome"):
        titlebar("welcome.exe")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='step'>{icon('envelope', 64)}1. Snap Dadi's letter</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='step'>{icon('heart', 50)}2. Understand every blessing</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='step'>{icon('open', 56)}3. Speak a reply, she hears it</div>", unsafe_allow_html=True)
        st.write("")
        a, b = st.columns(2)
        a.selectbox("Grandparent writes in", list(GP_LANGS), key="w_gp",
                    index=list(GP_LANGS).index(st.session_state.gp_name))
        b.selectbox("Grandkid reads", list(KID_LANGS), key="w_kid",
                    index=list(KID_LANGS).index(st.session_state.kid_name))
        key_in = None
        if not os.environ.get("SARVAM_API_KEY"):
            key_in = st.text_input("Sarvam API key", type="password")
        st.button("Open Chitthi", width="stretch", on_click=start, args=(key_in,),
                  disabled=not (os.environ.get("SARVAM_API_KEY") or key_in))
    footer()
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"<div style='text-align:center'>{icon('open', 70)}<h2 style='margin:0'>Chitthi</h2></div>",
                unsafe_allow_html=True)
    key = os.environ.get("SARVAM_API_KEY") or st.text_input(
        "Sarvam API key", type="password", value=st.session_state.get("api_key", ""))
    gp_name = st.selectbox("Grandparent's language", list(GP_LANGS), key="gp_name")
    kid_name = st.selectbox("Grandkid's language", list(KID_LANGS), key="kid_name")
    gp, kid = GP_LANGS[gp_name], KID_LANGS[kid_name]
    with st.container(key="win_apis"):
        titlebar("Sarvam APIs live")
        api_panel = st.empty()  # filled at the end so dots reflect this run's calls

st.markdown(f"<div class='hero'><h1>{icon('envelope', 60)} Chitthi</h1>"
            "<p><i>Families live in different scripts. Chitthi carries the letter across.</i></p></div>",
            unsafe_allow_html=True)

if not key:
    st.warning("Add your Sarvam API key in the sidebar (or set SARVAM_API_KEY).")
    st.stop()
client = SarvamAI(api_subscription_key=key)


# ---------- API helpers ----------
def to_pdf(upload):
    data = upload.getvalue()
    if upload.type == "application/pdf":
        return data
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).convert("RGB").save(buf, format="PDF")
    return buf.getvalue()


def vision(pdf_bytes, lang):
    job = client.doc_ai.digitise(file=[("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")],
                                 language=lang, content_type="handwritten")
    for _ in range(90):  # ~3 min max
        state = client.doc_ai.get_status(job_id=job.job_id).status.lower()
        if state in ("completed", "partially_completed"):
            break
        if state in ("failed", "rejected"):
            raise RuntimeError(f"Vision job {state}")
        time.sleep(2)
    else:
        raise TimeoutError("Vision took too long")
    dl = client.doc_ai.get_download_url(job_id=job.job_id)
    content = httpx.request(dl.method or "GET", dl.url, headers=dl.headers or {}, timeout=60).content
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            names = z.namelist()
            md = [n for n in names if n.endswith(".md")]
            if md:
                return z.read(md[0]).decode("utf-8")
            content = z.read(next(n for n in names if n.endswith(".html")))  # Vision now returns HTML
    return html_to_text(content.decode("utf-8"))


def html_to_text(s):
    s = re.sub(r"<(style|script|head).*?</\1>", "", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</(p|div|h\d|li|tr)>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def translate(text, target):
    r = client.text.translate(input=text[:2000], source_language_code="auto", target_language_code=target)
    return r.translated_text


def chat(prompt):
    for _ in range(2):  # model sometimes spends all tokens thinking and returns no content
        r = client.chat.completions(model="sarvam-105b", max_tokens=8000,
                                    messages=[{"role": "user", "content": prompt}])
        out = r.choices[0].message.content
        if out:
            return re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()
    raise RuntimeError("Sarvam-105B returned an empty answer, please try again")


def tts(text, lang):
    text = text[:2400]
    try:
        r = client.text_to_speech.convert(text=text, language_code=lang, model="bulbul:v3", speaker="shubh")
    except Exception:
        r = client.text_to_speech.convert(text=text, language_code=lang, model="bulbul:v4-flash", speaker="shubh")
    return base64.b64decode("".join(r.audios))


def stt(wav):
    r = client.speech_to_text.transcribe(file=("r.wav", wav, "audio/wav"), model="saaras:v4", mode="codemix")
    return r.transcript


tab1, tab2, tab3 = st.tabs(["Read Dadi's letter", "Reply to Dadi", "In Dadi's voice"])

# ---------- TAB 1 ----------
with tab1:
    left, right = st.columns([1, 1], gap="large")
    with left, st.container(key="win_upload"):
        titlebar("1 · open_letter.jpg")
        up = st.file_uploader("Upload a photo or PDF of Dadi's letter", type=["png", "jpg", "jpeg", "pdf"])
        if up:
            if up.type != "application/pdf":
                st.image(up, width="stretch")
            else:
                st.markdown(f"<div class='step'>{icon('folder', 70)}{html.escape(up.name)}</div>", unsafe_allow_html=True)
            if st.button("Read the handwriting", width="stretch"):
                with waiting("Sarvam Vision is reading Dadi's handwriting..."):
                    try:
                        st.session_state.orig = vision(to_pdf(up), gp)
                        mark("Sarvam Vision")
                    except Exception as e:
                        st.error(f"Couldn't read the letter: {e}. You can paste the text instead.")
        else:
            st.markdown(f"<div class='step'>{icon('envelope', 110)}Drop a letter above to begin</div>",
                        unsafe_allow_html=True)

    with right, st.container(key="win_text"):
        titlebar("2 · letter.txt")
        orig = st.text_area("Letter text (edit or paste here)", value=st.session_state.get("orig", ""), height=230)
        if st.button("Translate & explain", disabled=not orig.strip(), width="stretch"):
            with waiting(f"Translating to {kid_name}..."):
                try:
                    st.session_state.trans = translate(orig, kid)
                    mark("Sarvam Translate")
                except Exception as e:
                    st.error(f"Translation failed: {e}")
            with waiting("Sarvam-105B is understanding what Dadi means..."):
                try:
                    st.session_state.explain = chat(
                        f"This is a letter from a grandparent, written in {gp_name}:\n\n{orig}\n\n"
                        f"Reply in {kid_name}. Give two sections:\n"
                        "## Letter\nA warm, easy-to-read version of the letter for a young grandchild.\n"
                        "## What Dadi means\nA short bullet list explaining old phrases, blessings, "
                        "relations and cultural references in the letter.")
                    mark("Sarvam-105B")
                except Exception as e:
                    st.error(f"Explanation failed: {e}")

    if st.session_state.get("trans") or st.session_state.get("explain"):
        st.write("")
        with st.container(key="win_result"):
            titlebar("from_dadi_with_love.txt")
            if st.session_state.get("trans"):
                letter(st.session_state.trans)
                if st.button("Listen to the letter"):
                    with waiting("Bulbul is reading it aloud..."):
                        try:
                            st.session_state.trans_audio = tts(st.session_state.trans, kid)
                            mark("Bulbul TTS")
                        except Exception as e:
                            st.error(f"Audio failed: {e}")
                if st.session_state.get("trans_audio"):
                    st.audio(st.session_state.trans_audio, format="audio/wav")
            if st.session_state.get("explain"):
                h, body = st.columns([1, 8])
                h.markdown(icon("heart", 60), unsafe_allow_html=True)
                body.markdown(st.session_state.explain)

# ---------- TAB 2 ----------
with tab2:
    left, right = st.columns([1, 1], gap="large")
    with left, st.container(key="win_mic"):
        titlebar("1 · record_reply.wav")
        st.write("Speak your reply casually — Hinglish is totally fine!")
        rec = st.audio_input("Record your reply")
        if rec and st.button("Turn it into a letter", width="stretch"):
            with waiting("Saaras is listening..."):
                try:
                    st.session_state.said = stt(rec.getvalue())
                    mark("Saaras STT")
                except Exception as e:
                    st.error(f"Couldn't transcribe: {e}")
            if st.session_state.get("said"):
                with waiting(f"Writing a loving letter in {gp_name}..."):
                    try:
                        st.session_state.reply = chat(
                            f"A grandchild said this to their grandparent (casual Hinglish):\n\n"
                            f"{st.session_state.said}\n\n"
                            f"Rewrite it as a respectful, loving letter to the grandparent, in {gp_name} "
                            f"using the native {gp_name} script. Keep all the real news. Output only the letter.")
                        mark("Sarvam-105B")
                    except Exception as e:
                        st.error(f"Letter writing failed: {e}")
            if st.session_state.get("reply"):
                with waiting(f"Bulbul is reading it in {gp_name}..."):
                    try:
                        st.session_state.reply_audio = tts(st.session_state.reply, gp)
                        mark("Bulbul TTS")
                    except Exception as e:
                        st.error(f"Audio failed: {e}")
        if st.session_state.get("said"):
            st.markdown(f"**You said:** {html.escape(st.session_state.said)}")

    with right, st.container(key="win_reply"):
        titlebar("2 · to_dadi.txt")
        if st.session_state.get("reply"):
            letter(st.session_state.reply)
            if st.session_state.get("reply_audio"):
                st.audio(st.session_state.reply_audio, format="audio/wav")
            c1, c2 = st.columns(2)
            c1.download_button("Letter text", st.session_state.reply, "chitthi.txt", width="stretch")
            if st.session_state.get("reply_audio"):
                c2.download_button("Letter audio", st.session_state.reply_audio, "chitthi.wav", "audio/wav",
                                   width="stretch")
        else:
            st.markdown(f"<div class='step'>{icon('hourglass', 50)}Your letter will appear here</div>",
                        unsafe_allow_html=True)

# ---------- TAB 3 ----------
with tab3:
    _, mid, _ = st.columns([1, 3, 1])
    with mid, st.container(key="win_voice"):
        titlebar("dadi_voice.exe")
        st.write("Upload a short voice note of Dadi, and hear the letter in her own voice.")
        note = st.file_uploader("Dadi's voice note", type=["wav", "mp3", "m4a", "ogg"])
        text = st.session_state.get("trans") or st.session_state.get("reply", "")
        if note and text and st.button("Read it in Dadi's voice", width="stretch"):
            lang = kid if st.session_state.get("trans") else gp
            with waiting("Learning Dadi's voice..."):
                try:
                    v = client.voice_cloning.create_voice(file=(note.name, note.getvalue(), note.type),
                                                          name="dadi", language=lang)
                    out = client.voice_cloning.convert(voice_id=v.data.voice_id, text=text[:2400], language_code=lang)
                    st.audio(base64.b64decode(out.audio_b64), format="audio/wav")
                    mark("Voice Cloning")
                except Exception:
                    st.error("Voice cloning not enabled on this key.")
        elif not text:
            st.caption("First translate a letter (tab 1) or write a reply (tab 2).")

# ---------- API panel (rendered last so it includes this run's calls) ----------
used = st.session_state.used
api_panel.markdown(
    "".join(f"<div class='api'><span class='led {'on' if a in used else ''}'></span>{a}</div>" for a in APIS)
    + f"<div class='loadbar' style='margin-top:.6rem'><div style='width:{100 * len(used) // len(APIS)}%;animation:none'></div></div>"
    + f"<p style='text-align:center;font-weight:700;margin:.3rem 0 0'>{len(used)} / {len(APIS)} APIs used</p>",
    unsafe_allow_html=True)

footer()
