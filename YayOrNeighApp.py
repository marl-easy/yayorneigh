import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from geopy.geocoders import Nominatim
import openmeteo_requests
import requests_cache
from retry_requests import retry

# --- TRANSLATIONS -----------------------------------------------------------

translations = {
    "en": {
        "title": "🐴 Yay or Neigh Blanket Recommender",
        "location_prompt": "📍 Where is your horse located?",
        "clipped_prompt": "Is your horse clipped?",
        "yes": "Yes",
        "no": "No",
        "all_day_prompt": "Does the horse wear the blanket the whole day?",
        "start_time_prompt": "⏰ Turnout start time (HH:MM)",
        "end_time_prompt": "⏰ Turnout end time (HH:MM)",
        "select_day": "📆 Select day",
        "recommendation_for": "🎯 Recommendation for:",
        "min_temp": "🌡️ Min Temp",
        "max_precip": "🌧️ Max Precipitation",
        "warning_temp": "⚠️ Warning: Max temperature later today is {temp:.1f}°C. Remove blanket in the afternoon!",
        "no_data": "No data available.",
        "blanket_400g": "🐴 400g Outdoor Blanket",
        "blanket_300g": "🐴 300g Outdoor Blanket",
        "blanket_200_250g": "🐴 200–250g Outdoor Blanket",
        "blanket_150g": "🐴 150g Outdoor Blanket",
        "blanket_100g": "🐴 100g Outdoor Blanket",
        "blanket_0_50g_rain_sheet": "🐴 0–50g Rain Sheet",
        "blanket_150_200g": "🐴 150–200g Outdoor Blanket",
        "blanket_100_150g": "🐴 100–150g Outdoor Blanket",
        "blanket_50_100g": "🐴 50–100g Outdoor Blanket",
        "blanket_50g_rain_sheet": "🐴 50g Rain Sheet",
        "blanket_none": "🟢 No blanket",
        "blanket_none_sensitive": "🟢 No blanket (Rain Sheet if sensitive)",
        "rain_sheet_warning_heavy": "🐴 Rain Sheet (0g), due to warm weather and heavy rain",
        "rain_sheet_warning_precip": "🐴 Rain Sheet (0g), due to expected precipitation",
        "seven_day_forecast": "🗓️ 7-Day Blanket Forecast",
    },
    "de": {
        "title": "🐴 Yay or Neigh Deckenempfehlung",
        "location_prompt": "📍 Wo steht dein Pferd?",
        "clipped_prompt": "Ist dein Pferd geschoren?",
        "yes": "Ja",
        "no": "Nein",
        "all_day_prompt": "Trägt das Pferd die Decke den ganzen Tag?",
        "start_time_prompt": "⏰ Weidebeginn (HH:MM)",
        "end_time_prompt": "⏰ Weideende (HH:MM)",
        "select_day": "📆 Tag auswählen",
        "recommendation_for": "🎯 Empfehlung für:",
        "min_temp": "🌡️ Min Temperatur",
        "max_precip": "🌧️ Max Niederschlag",
        "warning_temp": "⚠️ Achtung: Max Temperatur später am Tag ist {temp:.1f}°C. Decke nachmittags abnehmen!",
        "no_data": "Keine Daten verfügbar.",
        "blanket_400g": "🐴 400g Outdoor-Decke",
        "blanket_300g": "🐴 300g Outdoor-Decke",
        "blanket_200_250g": "🐴 200–250g Outdoor-Decke",
        "blanket_150g": "🐴 150g Outdoor-Decke",
        "blanket_100g": "🐴 100g Outdoor-Decke",
        "blanket_0_50g_rain_sheet": "🐴 0–50g Regendecke",
        "blanket_150_200g": "🐴 150–200g Outdoor-Decke",
        "blanket_100_150g": "🐴 100–150g Outdoor-Decke",
        "blanket_50_100g": "🐴 50–100g Outdoor-Decke",
        "blanket_50g_rain_sheet": "🐴 50g Regendecke",
        "blanket_none": "🟢 Keine Decke",
        "blanket_none_sensitive": "🟢 Keine Decke (Regendecke bei empfindlichen Pferden)",
        "rain_sheet_warning_heavy": "🐴 Regendecke (0g), wegen warmem Wetter und starkem Regen",
        "rain_sheet_warning_precip": "🐴 Regendecke (0g), wegen erwartetem Niederschlag",
        "seven_day_forecast": "🗓️ 7-Tage Decken-Prognose",
    },
    "fr": {
        "title": "🐴 Recommandateur de Couvertures Yay or Neigh",
        "location_prompt": "📍 Où est situé votre cheval ?",
        "clipped_prompt": "Votre cheval est-il tondu ?",
        "yes": "Oui",
        "no": "Non",
        "all_day_prompt": "Le cheval porte-t-il la couverture toute la journée ?",
        "start_time_prompt": "⏰ Heure de sortie (HH:MM)",
        "end_time_prompt": "⏰ Heure de retour (HH:MM)",
        "select_day": "📆 Sélectionnez le jour",
        "recommendation_for": "🎯 Recommandation pour :",
        "min_temp": "🌡️ Temp. Min",
        "max_precip": "🌧️ Précipitations max",
        "warning_temp": "⚠️ Attention : La température max plus tard dans la journée est de {temp:.1f}°C. Retirez la couverture l'après-midi !",
        "no_data": "Pas de données disponibles.",
        "blanket_400g": "🐴 Couverture extérieure 400g",
        "blanket_300g": "🐴 Couverture extérieure 300g",
        "blanket_200_250g": "🐴 Couverture extérieure 200–250g",
        "blanket_150g": "🐴 Couverture extérieure 150g",
        "blanket_100g": "🐴 Couverture extérieure 100g",
        "blanket_0_50g_rain_sheet": "🐴 Couverture pluie 0–50g",
        "blanket_150_200g": "🐴 Couverture extérieure 150–200g",
        "blanket_100_150g": "🐴 Couverture extérieure 100–150g",
        "blanket_50_100g": "🐴 Couverture extérieure 50–100g",
        "blanket_50g_rain_sheet": "🐴 Couverture pluie 50g",
        "blanket_none": "🟢 Pas de couverture",
        "blanket_none_sensitive": "🟢 Pas de couverture (Couverture pluie si sensible)",
        "rain_sheet_warning_heavy": "🐴 Couverture pluie (0g), à cause de la pluie forte et du temps chaud",
        "rain_sheet_warning_precip": "🐴 Couverture pluie (0g), à cause des précipitations attendues",
        "seven_day_forecast": "🗓️ Prévision de couverture sur 7 jours",
    }
}

def t(key):
    return translations[st.session_state["lang"]].get(key, key)

# --- WEATHER FETCHING -------------------------------------------------------

@st.cache_data(show_spinner="Fetching weather data...")
def get_coordinates(location):
    geolocator = Nominatim(user_agent="YayOrNeighApp")
    loc = geolocator.geocode(location)
    if loc:
        return loc.latitude, loc.longitude, loc.address
    else:
        return None, None, None

@st.cache_data(show_spinner="Loading forecast...")
def get_weather_data(lat, lon):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "hourly": ["temperature_2m", "rain", "showers", "snowfall"],
        "forecast_days": 7
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    df = pd.DataFrame({
        "datetime": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature": hourly.Variables(0).ValuesAsNumpy(),
        "rain": hourly.Variables(1).ValuesAsNumpy(),
        "showers": hourly.Variables(2).ValuesAsNumpy(),
        "snowfall": hourly.Variables(3).ValuesAsNumpy()
    })
    df["datetime"] = df["datetime"].dt.tz_convert("Europe/Berlin")
    return df

# --- BLANKET LOGIC ----------------------------------------------------------

def choose_blanket(temp, clipped):
    if clipped:
        if temp < -10:
            return t("blanket_400g")
        elif temp < -5:
            return t("blanket_300g")
        elif temp < 0:
            return t("blanket_200_250g")
        elif temp < 5:
            return t("blanket_150g")
        elif temp < 10:
            return t("blanket_100g")
        elif temp < 15:
            return t("blanket_0_50g_rain_sheet")
        else:
            return t("blanket_none")
    else:
        if temp < -10:
            return t("blanket_200_250g")
        elif temp < -5:
            return t("blanket_150_200g")
        elif temp < 0:
            return t("blanket_100_150g")
        elif temp < 5:
            return t("blanket_50_100g")
        elif temp < 10:
            return t("blanket_50g_rain_sheet")
        elif temp < 15:
            return t("blanket_none_sensitive")
        else:
            return t("blanket_none")

def get_weather_icon(temp, rain):
    if rain > 2:
        return "🌧️"
    elif rain > 0:
        return "🌦️"
    elif temp > 25:
        return "☀️"
    elif temp > 18:
        return "🌤️"
    elif temp > 10:
        return "⛅"
    else:
        return "☁️"

def decide_blanket(df, day_index, clipped, start_time, end_time, all_day):
    date = (datetime.now().date() + timedelta(days=day_index))
    day_df = df[df["datetime"].dt.date == date]
    turnout_df = day_df[(day_df["datetime"].dt.time >= start_time) & (day_df["datetime"].dt.time <= end_time)]

    if turnout_df.empty:
        return t("no_data"), None, None, ""

    min_temp = turnout_df["temperature"].min()
    max_rain = turnout_df[["rain", "showers", "snowfall"]].sum(axis=1).max()
    blanket = choose_blanket(min_temp, clipped)

    if max_rain > 2 and min_temp > 15:
        blanket = t("rain_sheet_warning_heavy")
    elif max_rain > 0 and "No blanket" in blanket:
        blanket = t("rain_sheet_warning_precip")

    warning = ""
    if all_day:
        max_temp_day = day_df["temperature"].max()
        if max_temp_day > 18:
            warning = t("warning_temp").format(temp=max_temp_day)

    return blanket, min_temp, max_rain, warning

# --- UI ----------------------------------------------------------------------

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

lang = st.sidebar.selectbox("Select Language / Sprache auswählen / Sélectionnez la langue",
                            options=["en", "de", "fr"],
                            format_func=lambda x: {"en": "English", "de": "Deutsch", "fr": "Français"}[x])
st.session_state["lang"] = lang

st.set_page_config(t("title"), page_icon="🐴")
st.title(t("title"))

location = st.text_input(t("location_prompt"), value="Groß-Gerau")
lat, lon, address = get_coordinates(location)
if not lat:
    st.error(t("no_data"))
    st.stop()

st.success(f"✅ {address}")
weather_df = get_weather_data(lat, lon)

col1, col2 = st.columns(2)
with col1:
    clipped = st.radio(t("clipped_prompt"), [t("yes"), t("no")]) == t("yes")
    all_day = st.radio(t("all_day_prompt"), [t("yes"), t("no")]) == t("yes")

with col2:
    start_time_str = st.text_input(t("start_time_prompt"), "07:00")
    end_time_str = st.text_input(t("end_time_prompt"), "17:00")

try:
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
except ValueError:
    st.error("Invalid time format. Use HH:MM.")
    st.stop()

day_names = [t("select_day")]  # We'll ignore this one as a placeholder for slider format below
day_list = ["Today", "Tomorrow"] + [(datetime.now() + timedelta(days=i)).strftime("%A") for i in range(2, 7)]

# We want slider labels in the selected language — simplest is to translate the first two, keep rest as is
day_names = [
    {"en": "Today", "de": "Heute", "fr": "Aujourd'hui"},
    {"en": "Tomorrow", "de": "Morgen", "fr": "Demain"}
]

def translate_day(day_index):
    if day_index == 0:
        return day_names[0][lang]
    elif day_index == 1:
        return day_names[1][lang]
    else:
        # Use Python weekday names as fallback, not translated
        return day_list[day_index]

day_index = st.slider(t("select_day"), 0, 6, 0, format="%d")
st.markdown(f"### {t('recommendation_for')} **{translate_day(day_index)}**")

blanket, min_temp, max_rain, warning = decide_blanket(weather_df, day_index, clipped, start_time, end_time, all_day)

if blanket:
    st.success(f"**{blanket}**")
    if min_temp is not None and max_rain is not None:
        st.markdown(f"{t('min_temp')}: **{min_temp:.1f}°C**  \n{t('max_precip')}: **{max_rain:.1f} mm**")
    if warning:
        st.warning(warning)

# --- 7-DAY FORECAST ---------------------------------------------------------

st.markdown(f"### {t('seven_day_forecast')}")

days = []
icons = []
blankets = []
temps = []
precips = []

for i in range(7):
    date = datetime.now().date() + timedelta(days=i)
    day_name = translate_day(i)
    blanket, temp, precip, _ = decide_blanket(weather_df, i, clipped, start_time, end_time, False)
    icon = get_weather_icon(temp if temp is not None else 0, precip if precip is not None else 0)

    days.append(day_name)
    icons.append(icon)
    blankets.append(blanket)
    temps.append(f"{temp:.1f}°C" if temp is not None else "-")
    precips.append(f"{precip:.1f} mm" if precip is not None else "-")

forecast_html = f"""
<style>
table {{ width: 100%; border-collapse: collapse; border: none; }}
th, td {{ text-align: center; padding: 6px; font-size: 1rem; border: none; }}
</style>
<table>
<tr>{''.join(f'<th>{day}</th>' for day in days)}</tr>
<tr>{''.join(f'<td>{icon}</td>' for icon in icons)}</tr>
<tr>{''.join(f'<td>{b}</td>' for b in blankets)}</tr>
<tr>{''.join(f'<td>{t}</td>' for t in temps)}</tr>
<tr>{''.join(f'<td>{p}</td>' for p in precips)}</tr>
</table>
"""

st.markdown(forecast_html, unsafe_allow_html=True)
