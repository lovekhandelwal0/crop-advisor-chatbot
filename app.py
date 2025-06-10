import pandas as pd
import gradio as gr
import openai
from openai import OpenAI
import gdown

from dotenv import load_dotenv
import os

load_dotenv()  # 🔥 This loads variables from .env into the environment

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sheet_id  = "1JDb4J_pXzhfpryXizHe8v22PiRg6WFSA"
xlsx_url  = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
gdown.download(xlsx_url, "test.xlsx", quiet=False)

df = pd.read_excel("test.xlsx", sheet_name="Sheet1")
soil_types = df['Soil_Type'].dropna().unique().tolist()
weather_types = df['Weather_Condition'].dropna().unique().tolist()

def smart_crop_advisor(soil_type, rainfall, temperature, fertilizer, irrigation, weather):
    summary_text = ""
    for _, row in df.iterrows():
        summary_text += (
            f"- Crop: {row['Crop']}, Soil: {row['Soil_Type']}, Rainfall: {row['Rainfall_mm']}mm, "
            f"Temp: {row['Temperature_Celsius']}°C, Weather: {row['Weather_Condition']}, "
            f"Fertilizer: {row['Fertilizer_Used']}, Irrigation: {row['Irrigation_Used']}, "
            f"Yield: {row['Yield_tons_per_hectare']} tons/hectare\n"
        )

    user_conditions = (
        f"Soil: {soil_type or 'any'}, Max Rainfall: {rainfall or 'any'}mm, "
        f"Max Temp: {temperature or 'any'}°C, Fertilizer: {fertilizer or 'any'}, "
        f"Irrigation: {irrigation or 'any'}, Weather: {weather or 'any'}"
    )

    prompt = (
        f"A farmer provides these growing conditions:\n"
        f"{user_conditions}\n\n"
        f"Below is the dataset:\n{summary_text}\n"
        f"From this data, suggest the top 1–2 crops that best match these conditions and explain why. "
        f"Only use crops from the dataset. Be concise and realistic."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return "🌾 Recommended Crop(s):\n\n" + response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT API Error:\n{str(e)}"

iface = gr.Interface(
    fn=smart_crop_advisor,
    inputs=[
        gr.Dropdown(choices=[""] + soil_types, label="Soil Type"),
        gr.Number(label="Max Rainfall (mm)", precision=1),
        gr.Number(label="Max Temperature (°C)", precision=1),
        gr.Radio(choices=["", "Yes", "No"], label="Fertilizer Used"),
        gr.Radio(choices=["", "Yes", "No"], label="Irrigation Used"),
        gr.Dropdown(choices=[""] + weather_types, label="Weather Condition"),
    ],
    outputs="text",
    title="🌾 GPT-Powered Crop Advisor (Full Sheet Analysis)",
    description="GPT will analyze the entire crop dataset and suggest the best crop(s) based on your conditions."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=8080)
