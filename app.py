# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 13:00:44 2026

@author: eivind
"""
import streamlit as st
import random
import time
import qrcode
import base64
from streamlit_autorefresh import st_autorefresh
from PIL import Image


    
START_POINTS = 5000
GUESS_REWARD = 300
GUESS_PENALTY = 300
GUESS_TIME = 20
st.set_page_config(
    page_title="Drikkeleken",
    layout="wide"
)
st.markdown("""
<style>

/* PLAYER CARDS */

.player-card{
    text-align:center;
    padding:10px;
    border-radius:15px;
    background:rgba(0,0,0,0.5);
    backdrop-filter: blur(6px);
}

/* DARE CARD STACK */

.card-stack{
    position:relative;
    height:380px;
    margin-top:40px;
}

.dare-card{
    position:absolute;
    width:80%;
    left:10%;
    padding:50px;
    border-radius:25px;
    font-size:70px;
    text-align:center;
    font-weight:bold;
    background:#111;
    border:8px solid black;
    box-shadow:0 20px 40px rgba(0,0,0,0.6);
    transition:all 0.3s ease;
}

.card-back{
    top:40px;
    left:13%;
    opacity:0.5;
}

.card-top{
    top:0px;
    z-index:2;
}

/* SCOREBOARD */

.scoreboard{
    background:rgba(0,0,0,0.6);
    padding:20px;
    border-radius:15px;
}

/* ANIMATION */

@keyframes popin{
    0%{transform:scale(0.5);opacity:0;}
    100%{transform:scale(1);opacity:1;}
}

.dare-card{
    animation:popin 0.4s ease;
}

</style>
""", unsafe_allow_html=True)
# -------------------------
# SHARED GAME STATE
# -------------------------

@st.cache_resource
def get_game():
    return {
        "players": {},
        "points": {},
        "avatars": {},
        "phase": "lobby",
        "menu_options": [],
        "menu_prices": {},
        "votes": {},
        "active_menu": [],
        "dares": [],
        "history": [],
        "reveal": None
    }

game = get_game()



params = st.query_params

st_autorefresh(interval=2000)


# -------------------------
# IMAGE → BASE64 (for HTML)
# -------------------------

def img_to_base64(img):

    if img is None:
        return ""

    return base64.b64encode(img.getvalue()).decode()


# -------------------------
# QR CODE
# -------------------------

def show_qr():
    st.subheader("Bli med")
    #join_url = st.text_input("Skriv inn URL")
    #if join_url:
        # Generate the QR code
    qr_img = qrcode.make("https://drikkelek.streamlit.app/")
    
    # Convert it to RGB to ensure Streamlit can display it
    qr_rgb = qr_img.convert("RGB")
    
    # Display the converted image
    st.image(qr_rgb, width=250, caption="Scan for å bli med")




# --- FUNCTION TO SET LOCAL BACKGROUND ---
def set_bg_local(image_file):
    with open(image_file, "rb") as f:
        bin_str = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            
            /* High-Res Scaling Fixes */
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center center;
            
            /* Helps prevent blurring when scaling */
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }}

        /* Dark overlay remains to keep text sharp */
        [data-testid="stVerticalBlock"] {{
            background-color: rgba(0, 0, 0, 0.6);
            padding: 20px;
            border-radius: 15px;
        }}
        
        h1, h2, h3, p, span, label {{
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5); /* Adds contrast to text */
        }}
        
        /* Fjern hvit toppstripe (Streamlit header) */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        
        /* Remove vertical scrolling */
        html, body, [data-testid="stAppViewContainer"] {{
            min-height: 100vh;
            overflow-y: auto;
        }}

        

        /* Remove default padding */
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }}
        .player-card{{
            text-align:center;
            padding:10px;
            border-radius:15px;
            background:rgba(0,0,0,0.5);
            backdrop-filter: blur(6px);
            margin-bottom:20px;
        }}
        html {{
            font-size: 20px;
        }}
        
        </style>
        """,
        unsafe_allow_html=True
    )




# =========================
# LANDING PAGE (LOGIN)
# =========================

if "role" not in st.session_state:
    st.title("🍾 Velkommen til Drikkeleken")
    
    role_choice = st.radio("Hvem er du?", ["Select Role", "Host", "Player"], index=0)
    
    if role_choice == "Host":
        if st.button("Gå inn i host rommet"):
            st.session_state.role = "host"
            st.rerun()
            
    elif role_choice == "Player":
        player_name = st.text_input("Skriv inn navnet ditt:")
        if st.button("Join Game") and player_name:
            st.session_state.role = "player"
            st.session_state.player_name = player_name
            st.rerun()
    st.stop() # Stop execution here until they choose a role

# =========================
# HOST SCREEN
# =========================

if st.session_state.role == "host":


    with st.sidebar:

        st.title("🎛 Host Control")

        if st.button("Lobby"):
            game["phase"] = "lobby"
            st.rerun()

        if st.button("Menu Setup"):
            game["phase"] = "menu_setup"
            st.rerun()

        if st.button("Voting"):
            game["phase"] = "menu_vote"
            st.rerun()

        if st.button("Game"):
            game["phase"] = "game"
            st.rerun()

        
        st.divider()
        st.subheader("Punish Player")
        
        players = list(game["players"].keys())

        if players:
            target = st.selectbox("Player", players)
        else:
            st.info("No players yet")
        amount = st.number_input("Penalty",100,2000,300)
        
        if st.button("Apply Penalty"):
            game["points"][target] -= amount
            st.success("Penalty applied")
        
        if st.button("Reveal Sender"):

            unresolved = [d for d in game["dares"] if not d["resolved"]]
        
            if unresolved:
                dare = unresolved[-1]
        
                st.warning(f"Sender was: {dare['sender']}")
        
                dare["resolved"] = True
        
        if st.button("Restart Game"):

            game.clear()
        
            game.update({
                "players": {},
                "points": {},
                "avatars": {},
                "phase": "lobby",
                "menu_options": [],
                "menu_prices": {},
                "votes": {},
                "active_menu": [],
                "dares": [],
                "history": [],
                "reveal": None
            })
        
            st.rerun()
    phase = game["phase"]

    set_bg_local("background.jpg")

    # -------------------------
    # LOBBY SCREEN
    # -------------------------
    if phase == "lobby":

        st.title("🍾 Oppsett")

        show_qr()

        st.divider()

        st.header("Spillere")

        cols = st.columns(4)

        for i, p in enumerate(game["players"]):
            with cols[i % 4]:

                if p in game["avatars"]:
                    st.markdown('<div class="player-card">', unsafe_allow_html=True)

                    if game["avatars"][p]:
                        avatar = game["avatars"].get(p)

                        if avatar:
                            st.image(avatar, width=150)
                        else:
                            st.write("👤")
                    else:
                        st.write("👤")
                    
                    st.markdown(f"### {p}")
                    st.write(game["points"].get(p,0),"pts")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        if st.button("Gå til meny setup"):
            game["phase"] = "menu_setup"
            st.rerun()
    elif phase == "menu_setup":

        st.title("⚙️ Lag drikke meny")
    
        with st.form("add_dare_form"):
    
            new_dare = st.text_input("Drikke")
            new_price = st.number_input(
                "Straff for å bli tatt",
                min_value=100,
                step=100,
                value=300
            )
    
            add_btn = st.form_submit_button("Legg til")
    
            if add_btn and new_dare:
    
                game["menu_options"].append(new_dare)
                game["menu_prices"][new_dare] = new_price
    
        st.divider()
    
        st.header("Gjeldende meny")
    
        for d in game["menu_options"]:
            st.write(f"{d} — {game['menu_prices'][d]} pts")
    
        st.divider()
    
        if st.button("Start voting"):
            game["phase"] = "menu_vote"
            st.rerun()
            
    elif phase == "menu_vote":

        st.title("🗳 Valg")

        vote_count = {}

        for player in game["votes"]:
            for vote in game["votes"][player]:
                vote_count[vote] = vote_count.get(vote, 0) + 1

        for option in game["menu_options"]:
            st.write(option, "-", vote_count.get(option, 0))

        if st.button("Start Game"):

            sorted_votes = sorted(
                vote_count,
                key=vote_count.get,
                reverse=True
            )

            game["active_menu"] = sorted_votes[:4]
            game["phase"] = "game"
            st.rerun()
            
    elif phase == "game":

        st.title("🎯 Game")
        st.subheader("🏆 Scoreboard")

        scores = sorted(
            game["points"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        cols = st.columns(len(scores))
        
        for i,(player,pts) in enumerate(scores):
        
            with cols[i]:
        
                st.markdown(
                f"""
                <div class="scoreboard">
                <h3>{player}</h3>
                <h2>{pts}</h2>
                </div>
                """,
                unsafe_allow_html=True
                )
        unresolved = [d for d in game["dares"] if not d["resolved"]]

        for dare in unresolved[::-1]:  # newest first
        
            html = f"""
            <div class="dare-card card-top" style="position:relative; margin-top:20px;">
            {dare["target"]} må:<br>{dare["text"]}
            </div>
            """
        
            st.markdown(html, unsafe_allow_html=True)
            
            
    PHASE_FLOW = [
        "lobby",
        "menu_setup",
        "menu_vote",
        "game"
    ]
    
    with st.sidebar:
    
        if st.button("⬅ Back Phase"):
            
            idx = PHASE_FLOW.index(game["phase"])
    
            if idx > 0:
                game["phase"] = PHASE_FLOW[idx-1]
    
            st.rerun()



# =========================
# PLAYER SCREEN
# =========================

elif st.session_state.role == "player":

    name = st.session_state.player_name

    if name not in game["players"]:

        game["players"][name] = True
        game["points"][name] = START_POINTS

    st.title(f"Player: {name}")
    st.write("Points:", game["points"][name])

# -------------------------
# TAKE SELFIE
# -------------------------

    if name not in game["avatars"]:

        st.subheader("Ta bilde (valgfritt)")
    
        photo = st.camera_input("Ta en selfie")
    
        col1, col2 = st.columns(2)
    
        with col1:
            if photo is not None:
                game["avatars"][name] = photo
                st.success("Bilde lagret")
                st.rerun()
    
        with col2:
            if st.button("Hopp over"):
                game["avatars"][name] = None
                st.rerun()
    
        st.stop()

# -------------------------
# LOBBY
# -------------------------
    phase = game["phase"]
    if phase == "lobby":

        st.info("Venter på host")
        
    

# -------------------------
# MENU VOTING
# -------------------------

    elif phase == "menu_vote":

        picks = st.multiselect(
            "Stem på drikke",
            game["menu_options"]
        )

        if st.button("Send inn stemmer"):

            game["votes"][name] = picks
            st.success("Stemmer lagret")

# -------------------------
# GAMEPLAY
# -------------------------

    elif phase == "game":

        st.header("Send drikke")

        targets = [p for p in game["players"] if p != name]

        cols = st.columns(4)

        for i, p in enumerate(targets):

            with cols[i % 4]:

                avatar = game["avatars"].get(p)

                if avatar:
                    st.image(avatar, width=120)
                else:
                    st.write("👤")

                if st.button(p, key=f"target_{p}"):

                    st.session_state.target = p

        if "target" in st.session_state:

            target = st.session_state.target

            for dare in game["active_menu"]:

                if st.button(dare):

                    game["dares"].append({
                        "sender": name,
                        "target": target,
                        "text": dare,
                        "resolved": False,
                        "time": time.time()
                    })

                    st.success("Drikke sendt")

# -------------------------
# RECEIVED DARES
# -------------------------

        st.divider()

        st.header("Du må:")

        for i, dare in enumerate(game["dares"]):

            if dare["target"] == name and not dare["resolved"]:

                st.warning(dare["text"])

                elapsed = time.time() - dare["time"]
                remaining = int(GUESS_TIME - elapsed)

                if remaining > 0:
                    st.write("Time left:", remaining)

                possible = [
                    p for p in game["players"]
                    if p != name
                ]

                options = random.sample(
                    possible,
                    min(4, len(possible))
                )

                if dare["sender"] not in options:
                    options[0] = dare["sender"]

                random.shuffle(options)

                cols = st.columns(len(options))

                for idx, player in enumerate(options):

                    with cols[idx]:

                        avatar = game["avatars"].get(player)

                        if avatar:
                            st.image(avatar, width=100)
                        else:
                            st.write("👤")

                        if st.button(player, key=f"guess{i}_{idx}"):

                            # Inside the player guess button logic:
                            if player == dare["sender"]:
                                st.balloons()
                                st.success("Riktig!")
                                # Use the custom price set by the host
                                penalty = game["menu_prices"].get(dare["text"], 300) 
                                
                                game["points"][name] += GUESS_REWARD
                                game["points"][player] -= penalty
                                result = f"{name} guessed {player} (Penalty: {penalty})"


                            else:

                                st.error("Feil!")

                                game["points"][name] -= GUESS_PENALTY

                                result = f"{name} failed to guess {dare['sender']}"

                            game["history"].append(result)

                            game["reveal"] = {
                                "sender": dare["sender"]
                            }

                            dare["resolved"] = True


