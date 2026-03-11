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
        "menu_options": [
            "Sing a song",
            "10 pushups",
            "Dance 30s",
            "Embarrassing story",
            "Speak in accent",
            "Act like a chicken"
        ],
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

    join_url = st.text_input("Join URL")

    if join_url:

        qr = qrcode.make(join_url)
        st.image(qr, width=250)


# =========================
# HOST SCREEN
# =========================

if "host" in params:

    st.title("🎮 Dare Game Host")

    if st.button("Reset Game"):

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

    st.header("Players")

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

    if game["phase"] == "lobby":

        if st.button("Start Menu Voting"):
            game["phase"] = "menu_vote"

    elif game["phase"] == "menu_vote":

        st.header("Menu Votes")

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

    st.header("Round History")

    for item in reversed(game["history"]):

        st.write(item)


# =========================
# PLAYER SCREEN
# =========================

elif "player" in params:

    name = params["player"]

    if name not in game["players"]:

        game["players"][name] = True
        game["points"][name] = START_POINTS

    st.title(f"Player: {name}")
    st.write("Points:", game["points"][name])

# -------------------------
# TAKE SELFIE
# -------------------------

    if name not in game["avatars"]:

        st.subheader("Take your player photo")

        photo = st.camera_input("Take a selfie")

        if photo is not None:

            game["avatars"][name] = photo
            st.success("Photo saved!")

        st.stop()

    phase = game["phase"]

# -------------------------
# LOBBY
# -------------------------

    if phase == "lobby":

        st.info("Waiting for host")

# -------------------------
# MENU VOTING
# -------------------------

    elif phase == "menu_vote":

        picks = st.multiselect(
            "Vote for dares",
            game["menu_options"]
        )

        if st.button("Submit Votes"):

            game["votes"][name] = picks
            st.success("Votes saved")

# -------------------------
# GAMEPLAY
# -------------------------

    elif phase == "game":

        st.header("Send Dare")

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

                    st.success("Dare sent")

# -------------------------
# RECEIVED DARES
# -------------------------

        st.divider()

        st.header("Dares You Received")

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

                            if player == dare["sender"]:

                                st.success("Correct!")

                                game["points"][name] += GUESS_REWARD
                                game["points"][player] -= GUESS_PENALTY

                                result = f"{name} guessed {player}"

                            else:

                                st.error("Wrong!")

                                game["points"][name] -= GUESS_PENALTY

                                result = f"{name} failed to guess {dare['sender']}"

                            game["history"].append(result)

                            game["reveal"] = {
                                "sender": dare["sender"]
                            }

                            dare["resolved"] = True


# =========================
# LANDING PAGE
# =========================

else:

    st.title("🎮 Dare Game")

    st.write("Join using:")

    st.code("?player=YourName")

    st.write("Host screen:")

    st.code("?host=true")