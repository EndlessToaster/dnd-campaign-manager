

import streamlit as st
import json
import random
import os
from datetime import datetime
import time
from openai import OpenAI
import requests
import re
import pandas as pd
import numpy as np

# Simple AI Configuration
class AIConfig:
    def __init__(self):
        self.providers = {
            "groq": {
                "api_key": os.getenv('GROQ_API_KEY', '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'),
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama3-70b-8192"],
                "default_model": "llama3-70b-8192",
                "status": "active"
            },
            "deepseek": {
                "api_key": os.getenv('DEEPSEEK_API_KEY', 'sk-063b2d5e7bda475e91eef1f2bedd0b33'),
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat"],
                "default_model": "deepseek-chat",
                "status": "active"
            }
        }

ai_config = AIConfig()

# Simple AI Manager
class SimpleAIManager:
    def __init__(self):
        self.conversation_history = []
    
    def ask_dm(self, prompt, character=None, campaign=None):
        try:
            # Try Groq first
            provider = ai_config.providers["groq"]
            client = OpenAI(
                api_key=provider["api_key"],
                base_url=provider["base_url"]
            )
            
            response = client.chat.completions.create(
                model=provider["default_model"],
                messages=[
                    {"role": "system", "content": "You are a helpful D&D Dungeon Master."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I apologize, but I'm having trouble connecting right now. Error: {str(e)}"

# Initialize AI
ai_manager = SimpleAIManager()

# App Configuration
CONFIG = {
    "CHARACTERS_DIR": "characters",
    "CAMPAIGNS_DIR": "campaigns",
    "DEFAULT_CHARACTER": {
        "name": "New Hero", "level": 1, "hp": 10, "max_hp": 10,
        "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10,
        "race": "Human", "class": "Fighter", "xp": 0
    }
}

# Create directories
os.makedirs(CONFIG["CHARACTERS_DIR"], exist_ok=True)
os.makedirs(CONFIG["CAMPAIGNS_DIR"], exist_ok=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "Home"
if 'character' not in st.session_state:
    st.session_state.character = CONFIG["DEFAULT_CHARACTER"].copy()
if 'current_campaign' not in st.session_state:
    st.session_state.current_campaign = {"name": "", "log": []}
if 'dm_messages' not in st.session_state:
    st.session_state.dm_messages = []

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# Utility functions
def calculate_ability_modifier(score):
    return (score - 10) // 2

def roll_dice(dice_string):
    try:
        pattern = r'(\d+)d(\d+)([\+\-]\d+)?'
        match = re.match(pattern, dice_string)
        if not match:
            return None
        num_dice = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3) or 0)
        rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        return {'total': total, 'rolls': rolls, 'modifier': modifier, 'dice_string': dice_string}
    except:
        return None

# Pages
def home_page():
    st.title("🎲 D&D Campaign Manager")
    st.subheader("Your AI-Powered Dungeon Master")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Quick Access")
        if st.button("🎭 Character Manager", use_container_width=True):
            navigate_to("Characters")
        if st.button("📖 Campaign Manager", use_container_width=True):
            navigate_to("Campaigns")
        if st.button("🧙‍♂️ AI Dungeon Master", use_container_width=True):
            navigate_to("AI DM")
        if st.button("🎯 Dice Roller", use_container_width=True):
            navigate_to("Dice")
    
    with col2:
        st.header("Current Session")
        if st.session_state.character['name'] != "New Hero":
            st.success(f"**Character:** {st.session_state.character['name']}")
            st.write(f"Level {st.session_state.character['level']} {st.session_state.character['class']}")
        else:
            st.info("No active character")
        
        if st.session_state.current_campaign['name']:
            st.success(f"**Campaign:** {st.session_state.current_campaign['name']}")
        else:
            st.info("No active campaign")

def character_manager_page():
    st.title("🎭 Character Manager")
    
    st.subheader("Create New Character")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Character Name", st.session_state.character['name'])
        race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Halfling", "Gnome"])
        char_class = st.selectbox("Class", ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian"])
    
    with col2:
        level = st.number_input("Level", 1, 20, st.session_state.character['level'])
        hp = st.number_input("HP", 1, 200, st.session_state.character['hp'])
        max_hp = st.number_input("Max HP", 1, 200, st.session_state.character['max_hp'])
    
    if st.button("Save Character"):
        st.session_state.character.update({
            'name': name, 'race': race, 'class': char_class,
            'level': level, 'hp': hp, 'max_hp': max_hp
        })
        st.success("Character saved!")

def campaign_manager_page():
    st.title("📖 Campaign Manager")
    
    st.subheader("Campaign Setup")
    campaign_name = st.text_input("Campaign Name", st.session_state.current_campaign['name'])
    
    if st.button("Create/Save Campaign"):
        st.session_state.current_campaign['name'] = campaign_name
        st.success("Campaign saved!")
    
    st.subheader("Campaign Log")
    new_entry = st.text_area("Add Log Entry")
    if st.button("Add Entry") and new_entry:
        if 'log' not in st.session_state.current_campaign:
            st.session_state.current_campaign['log'] = []
        st.session_state.current_campaign['log'].append({
            'timestamp': datetime.now().isoformat(),
            'message': new_entry
        })
        st.success("Entry added!")
    
    if st.session_state.current_campaign.get('log'):
        st.write("Recent Entries:")
        for entry in reversed(st.session_state.current_campaign['log'][-5:]):
            st.write(f"- {entry['message']}")

def ai_dm_page():
    st.title("🧙‍♂️ AI Dungeon Master")
    
    if not st.session_state.current_campaign['name']:
        st.warning("Please create a campaign first!")
        return
    
    st.subheader("💬 Conversation with DM")
    
    # Display conversation
    for msg in st.session_state.dm_messages[-10:]:
        st.write(f"**You:** {msg.get('input', '')}")
        st.write(f"**DM:** {msg.get('response', '')}")
        st.markdown("---")
    
    # Input
    player_input = st.text_area("What would you like to do?", height=100)
    
    if st.button("Ask the DM") and player_input:
        with st.spinner("DM is thinking..."):
            response = ai_manager.ask_dm(player_input, st.session_state.character, st.session_state.current_campaign)
            st.session_state.dm_messages.append({
                'input': player_input,
                'response': response
            })
        st.rerun()

def dice_roller_page():
    st.title("🎯 Dice Roller")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Common Rolls")
        if st.button("d20", use_container_width=True):
            result = roll_dice("1d20")
            st.session_state.dice_result = result
        
        if st.button("2d6", use_container_width=True):
            result = roll_dice("2d6")
            st.session_state.dice_result = result
        
        if st.button("3d6", use_container_width=True):
            result = roll_dice("3d6")
            st.session_state.dice_result = result
        
        st.subheader("Custom Roll")
        custom_dice = st.text_input("Dice (e.g., 2d8+3)")
        if st.button("Roll Custom") and custom_dice:
            result = roll_dice(custom_dice)
            st.session_state.dice_result = result
    
    with col2:
        st.subheader("Results")
        if hasattr(st.session_state, 'dice_result') and st.session_state.dice_result:
            result = st.session_state.dice_result
            st.success(f"**Total:** {result['total']}")
            st.write(f"**Rolls:** {result['rolls']}")
            if result['modifier'] != 0:
                st.write(f"**Modifier:** {result['modifier']:+d}")
        else:
            st.info("Roll some dice to see results here!")

# Main app
def main():
    st.set_page_config(
        page_title="D&D Campaign Manager",
        page_icon="🎲",
        layout="wide"
    )
    
    # Sidebar
    with st.sidebar:
        st.title("🎲 Navigation")
        pages = ["Home", "Characters", "Campaigns", "AI DM", "Dice"]
        selected = st.selectbox("Go to", pages, index=pages.index(st.session_state.page))
        if selected != st.session_state.page:
            navigate_to(selected)
        
        st.markdown("---")
        if st.session_state.character['name'] != "New Hero":
            st.success(f"Active: {st.session_state.character['name']}")
    
    # Page routing
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Characters":
        character_manager_page()
    elif st.session_state.page == "Campaigns":
        campaign_manager_page()
    elif st.session_state.page == "AI DM":
        ai_dm_page()
    elif st.session_state.page == "Dice":
        dice_roller_page()

if __name__ == "__main__":
    main()