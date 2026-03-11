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

# Constant rewards, but penalties are now dynamic
START_POINTS = 5000
GUESS_REWARD = 300
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
        "menu_options": [],   # Dynamically filled by host
        "menu_prices": {},    # Stores penalty per dare
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
# HELPERS
# -------------------------

def img_to_base64(img):
    if img is None: return ""
    return base64.b64encode(img.getvalue()).decode()

def show_qr():
    st.subheader("Join Game")
    join_url = st.text_input("Join URL (Enter your app URL here)")
    if join_url:
        qr = qrcode.make(join_url)
        st.image(qr, width=250)

# =========================
# HOST SCREEN
# =========================

if "host" in params:
    st.title("🎮 Dare Game Host")

    if st.button("Reset Game"):
        game.update({
            "players": {}, "points": {}, "avatars": {}, "votes": {},
            "dares": [], "history": [], "reveal": None, "phase": "lobby",
            "menu_options": [], "menu_prices": {}
        })
        st.rerun()

    show_qr()
    st.divider()

    # --- PLAYER LOBBY ---
    st.header("Players")
    cols = st.columns(4)
    for i, p in enumerate(game["players"]):
        with cols[i % 4]:
            if p in game["avatars"]:
                st.image(game["avatars"][p], width=140)
            st.markdown(f"### {p}")
            st.write("Points:", game["points"][p])

    st.divider()

    # --- PHASE CONTROL & SETUP ---
    st.write("Current Phase:", game["phase"].upper())

    if game["phase"] == "lobby":
        st.subheader("🛠️ Setup Dares & Prices")
        with st.form("dare_config"):
            d_text = st.text_input("Dare Description (e.g. Do 10 pushups)")
            d_price = st.number_input("Penalty if caught (Points)", min_value=0, value=300, step=50)
            add = st.form_submit_button("Add Dare")
            if add and d_text:
                game["menu_options"].append(d_text)
                game["menu_prices"][d_text] = d_price
                st.success(f"Added '{d_text}' with {d_price} point penalty.")

        if game["menu_options"]:
            st.write("Current Menu:")
            for opt in game["menu_options"]:
                st.write(f"- {opt} ({game['menu_prices'][opt]} pts)")

        if st.button("Start Menu Voting", disabled=len(game["menu_options"]) < 2):
            game["phase"] = "menu_vote"
            st.rerun()

    elif game["phase"] == "menu_vote":
        st.header("Menu Votes")
        vote_count = {}
        for p_votes in game["votes"].values():
            for v in p_votes:
                vote_count[v] = vote_count.get(v, 0) + 1
        
        for option in game["menu_options"]:
            st.write(f"{option}: {vote_count.get(option, 0)} votes")

        if st.button("Start Game"):
            sorted_votes = sorted(vote_count, key=vote_count.get, reverse=True)
            game["active_menu"] = sorted_votes[:4] if sorted_votes else game["menu_options"][:4]
            game["phase"] = "game"
            st.rerun()

    elif game["phase"] == "game":
        unresolved = [d for d in game["dares"] if not d["resolved"]]
        if unresolved:
            dare = unresolved[-1]
            st.markdown(f"""
                <div style="text-align:center; font-size:50px; font-weight:bold; padding:30px; background:#111; color:white; border-radius:20px;">
                {dare["target"]} must:<br>{dare["text"]}
                </div>
            """, unsafe_allow_html=True)

    if game["reveal"]:
        sender = game["reveal"]["sender"]
        if sender in game["avatars"]:
            img64 = img_to_base64(game["avatars"][sender])
            st.markdown(f"""
                <div style="text-align:center; margin-top:20px;">
                <h1>REVEALED!</h1>
                <img src="data:image/png;base64,{img64}" style="width:250px; border-radius:20px;">
                <h2>It was {sender}!</h2>
                </div>
            """, unsafe_allow_html=True)

    st.header("History")
    for item in reversed(game["history"]): st.write(item)

# =========================
# PLAYER SCREEN
# =========================

elif "player" in params:
    name = params["player"]
    if name not in game["players"]:
        game["players"][name] = True
        game["points"][name] = START_POINTS

    st.title(f"Player: {name}")
    st.subheader(f"Points: {game['points'][name]}")

    if name not in game["avatars"]:
        photo = st.camera_input("Take a selfie to join")
        if photo:
            game["avatars"][name] = photo
            st.rerun()
        st.stop()

    # --- PLAYER PHASES ---
    if game["phase"] == "lobby":
        st.info("Waiting for host to set the dares...")

    elif game["phase"] == "menu_vote":
        picks = st.multiselect("Vote for the dares you want in the game:", game["menu_options"])
        if st.button("Submit Votes"):
            game["votes"][name] = picks
            st.success("Votes saved!")

    elif game["phase"] == "game":
        st.header("Send a Dare")
        targets = [p for p in game["players"] if p != name]
        t_cols = st.columns(4)
        for i, p in enumerate(targets):
            with t_cols[i % 4]:
                if p in game["avatars"]: st.image(game["avatars"][p], width=100)
                if st.button(p, key=f"btn_{p}"): st.session_state.target = p

        if "target" in st.session_state:
            target = st.session_state.target
            st.write(f"Sending dare to: **{target}**")
            for dare_text in game["active_menu"]:
                penalty = game["menu_prices"].get(dare_text, 300)
                if st.button(f"{dare_text} (-{penalty} pts)"):
                    game["dares"].append({
                        "sender": name, "target": target, "text": dare_text,
                        "resolved": False, "time": time.time()
                    })
                    st.success("Dare sent!")
                    del st.session_state.target
                    st.rerun()

        # --- RECEIVED DARES ---
        st.divider()
        st.header("Dares Received")
        for i, dare in enumerate(game["dares"]):
            if dare["target"] == name and not dare["resolved"]:
                st.warning(f"ACTION REQUIRED: {dare['text']}")
                
                remaining = int(GUESS_TIME - (time.time() - dare["time"]))
                if remaining > 0:
                    st.write(f"Time to guess: {remaining}s")
                    possible = [p for p in game["players"] if p != name]
                    options = random.sample(possible, min(4, len(possible)))
                    if dare["sender"] not in options: options[0] = dare["sender"]
                    random.shuffle(options)

                    g_cols = st.columns(len(options))
                    for idx, opt_p in enumerate(options):
                        with g_cols[idx]:
                            if opt_p in game["avatars"]: st.image(game["avatars"][opt_p], width=80)
                            if st.button(opt_p, key=f"g_{i}_{idx}"):
                                penalty = game["menu_prices"].get(dare["text"], 300)
                                if opt_p == dare["sender"]:
                                    st.success("Correct!")
                                    game["points"][name] += GUESS_REWARD
                                    game["points"][opt_p] -= penalty
                                    res = f"✅ {name} caught {opt_p}! ({opt_p} lost {penalty})"
                                else:
                                    st.error("Wrong!")
                                    game["points"][name] -= penalty
                                    res = f"❌ {name} guessed wrong! ({name} lost {penalty})"
                                
                                game["history"].append(res)
                                game["reveal"] = {"sender": dare["sender"]}
                                dare["resolved"] = True
                                st.rerun()
                else:
                    st.error("Time up! You failed to guess.")
                    dare["resolved"] = True

else:
    st.title("🎮 Dare Game")
    st.write("Join as a player: `?player=Name`")
    st.write("Open host screen: `?host=true`")
