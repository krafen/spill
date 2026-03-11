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

START_POINTS = 5000
GUESS_REWARD = 300
GUESS_PENALTY = 300
GUESS_TIME = 20


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
        "menu_options": [],  # Start empty
        "menu_prices": {},   # New: Store price per dare
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
    st.subheader("Join Game")
    join_url = st.text_input("Join URL (Enter your app URL here)")
    if join_url:
        # Generate the QR code
        qr_img = qrcode.make(join_url)
        
        # Convert it to RGB to ensure Streamlit can display it
        qr_rgb = qr_img.convert("RGB")
        
        # Display the converted image
        st.image(qr_rgb, width=250, caption="Scan to join the game!")


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

    st.title("Hostens drikkelek")

    if game["phase"] == "lobby":
        st.subheader("Hva skal vi bli drita på i dag?")
        
        with st.form("add_dare_form"):
            new_dare = st.text_input("Drikke:")
            new_price = st.number_input("Straff for å bli tatt", min_value=100, step=100, value=300)
            add_btn = st.form_submit_button("Legg til")
            
            if add_btn and new_dare:
                if new_dare not in game["menu_options"]:
                    game["menu_options"].append(new_dare)
                    game["menu_prices"][new_dare] = new_price
                    st.success(f"Added: {new_dare} ({new_price} pts)")
    
        # Show current menu
        if game["menu_options"]:
            st.write("Gjeldende meny:")
            for d in game["menu_options"]:
                st.write(f"- {d}: {game['menu_prices'][d]} pts")
    
        if st.button("Stem på det som skal være med", disabled=len(game["menu_options"]) < 2):
            game["phase"] = "menu_vote"


    if st.button("Start på nytt"):

        game["players"].clear()
        game["points"].clear()
        game["avatars"].clear()
        game["votes"].clear()
        game["dares"].clear()
        game["history"].clear()
        game["reveal"] = None
        game["phase"] = "lobby"

    show_qr()

    st.divider()

# -------------------------
# PLAYER BOARD
# -------------------------

    st.header("Spillere")

    cols = st.columns(4)

    for i, p in enumerate(game["players"]):

        with cols[i % 4]:

            if p in game["avatars"]:
                st.image(game["avatars"][p], width=140)

            st.markdown(f"### {p}")
            st.write("Points:", game["points"][p])

    st.divider()

# -------------------------
# PHASE CONTROL
# -------------------------

    st.write("Phase:", game["phase"])

    

    if game["phase"] == "menu_vote":

      st.header("Stemmer")

      vote_count = {}

      for player in game["votes"]:
          for vote in game["votes"][player]:
              vote_count[vote] = vote_count.get(vote, 0) + 1

      for option in game["menu_options"]:
          st.write(option, "-", vote_count.get(option, 0))

      if st.button("Start drikkinga"):

          sorted_votes = sorted(
              vote_count,
              key=vote_count.get,
              reverse=True
          )

          game["active_menu"] = sorted_votes[:4]
          game["phase"] = "game"

# -------------------------
# BIG SCREEN DARE DISPLAY
# -------------------------

    elif game["phase"] == "game":

        unresolved = [d for d in game["dares"] if not d["resolved"]]

        if unresolved:

            dare = unresolved[-1]

            st.markdown(
                f"""
                <div style="
                text-align:center;
                font-size:60px;
                font-weight:bold;
                padding:40px;
                background:#111;
                color:white;
                border-radius:20px;">
                {dare["target"]} must:<br>{dare["text"]}
                </div>
                """,
                unsafe_allow_html=True
            )

# -------------------------
# REVEAL SCREEN
# -------------------------

    if game["reveal"]:

        sender = game["reveal"]["sender"]

        if sender in game["avatars"]:

            img64 = img_to_base64(game["avatars"][sender])

            st.markdown(
                f"""
                <div style="
                text-align:center;
                margin-top:40px;">
                <h1>REVEAL</h1>
                <img src="data:image/png;base64,{img64}" 
                style="width:300px;border-radius:20px;">
                <h2>{sender}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

# -------------------------
# HISTORY
# -------------------------

    st.header("Runde Historikk")

    for item in reversed(game["history"]):

        st.write(item)


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

        st.subheader("Ta bilde")

        photo = st.camera_input("Ta en selfie")

        if photo is not None:

            game["avatars"][name] = photo
            st.success("Bilde lagret")

        st.stop()

    phase = game["phase"]

# -------------------------
# LOBBY
# -------------------------

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

                st.image(game["avatars"][p], width=120)

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

                        st.image(game["avatars"][player], width=100)

                        if st.button(player, key=f"guess{i}_{idx}"):

                            # Inside the player guess button logic:
                            if player == dare["sender"]:
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


