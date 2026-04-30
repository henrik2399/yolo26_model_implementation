"""
detector.py — YOLOv8 Objekterkennung
Läuft automatisch auf GPU (lokal) oder CPU (Streamlit Cloud).
"""
import numpy as np
from PIL import Image
import streamlit as st

# ── Kategorie-Mapping ─────────────────────────────────────────
CATEGORIES = [
    "Schreibwaren",
    "Kleidung",
    "Elektronik",
    "Taschen & Rucksäcke",
    "Sportartikel",
    "Essen & Trinken",
    "Bücher & Hefte",
    "Schmuck & Accessoires",
    "Schlüssel",
    "Sonstiges",
]

CATEGORY_ICONS = {
    "Schreibwaren":         "✏️",
    "Kleidung":             "👕",
    "Elektronik":           "📱",
    "Taschen & Rucksäcke":  "🎒",
    "Sportartikel":         "⚽",
    "Essen & Trinken":      "🍶",
    "Bücher & Hefte":       "📚",
    "Schmuck & Accessoires":"💍",
    "Schlüssel":            "🔑",
    "Sonstiges":            "📦",
}

CATEGORY_COLORS = {
    "Schreibwaren":         "#4A90D9",
    "Kleidung":             "#E8724A",
    "Elektronik":           "#7B68EE",
    "Taschen & Rucksäcke":  "#27AE60",
    "Sportartikel":         "#F39C12",
    "Essen & Trinken":      "#E74C3C",
    "Bücher & Hefte":       "#16A085",
    "Schmuck & Accessoires":"#9B59B6",
    "Schlüssel":            "#D4AC0D",
    "Sonstiges":            "#7F8C8D",
}

YOLO_TO_CATEGORY = {
    "pen": "Schreibwaren", "pencil": "Schreibwaren",
    "scissors": "Schreibwaren", "ruler": "Schreibwaren",
    "book": "Bücher & Hefte", "notebook": "Bücher & Hefte",
    "tie": "Kleidung", "jacket": "Kleidung", "coat": "Kleidung",
    "glove": "Kleidung", "hat": "Kleidung", "umbrella": "Kleidung",
    "cell phone": "Elektronik", "laptop": "Elektronik",
    "keyboard": "Elektronik", "mouse": "Elektronik",
    "remote": "Elektronik", "headphones": "Elektronik",
    "backpack": "Taschen & Rucksäcke", "handbag": "Taschen & Rucksäcke",
    "suitcase": "Taschen & Rucksäcke",
    "sports ball": "Sportartikel", "frisbee": "Sportartikel",
    "tennis racket": "Sportartikel", "baseball bat": "Sportartikel",
    "skateboard": "Sportartikel", "bicycle": "Sportartikel",
    "skis": "Sportartikel", "snowboard": "Sportartikel",
    "bottle": "Essen & Trinken", "cup": "Essen & Trinken",
    "bowl": "Essen & Trinken", "fork": "Essen & Trinken",
    "knife": "Essen & Trinken", "spoon": "Essen & Trinken",
    "banana": "Essen & Trinken", "apple": "Essen & Trinken",
    "orange": "Essen & Trinken", "sandwich": "Essen & Trinken",
    "pizza": "Essen & Trinken", "donut": "Essen & Trinken",
    "cake": "Essen & Trinken", "hot dog": "Essen & Trinken",
}

LABEL_DE = {
    "backpack": "Rucksack", "bottle": "Trinkflasche",
    "cell phone": "Handy", "laptop": "Laptop",
    "book": "Buch", "pencil": "Bleistift", "pen": "Stift",
    "umbrella": "Regenschirm", "handbag": "Handtasche",
    "suitcase": "Koffer", "scissors": "Schere",
    "cup": "Tasse", "sports ball": "Ball",
    "keyboard": "Tastatur", "mouse": "Maus",
    "remote": "Fernbedienung", "tie": "Krawatte",
    "hat": "Hut", "glove": "Handschuh",
    "jacket": "Jacke", "coat": "Mantel",
    "frisbee": "Frisbee", "skateboard": "Skateboard",
    "tennis racket": "Tennisschläger",
    "baseball bat": "Baseballschläger",
    "bicycle": "Fahrrad", "bowl": "Schüssel",
    "fork": "Gabel", "knife": "Messer", "spoon": "Löffel",
    "banana": "Banane", "apple": "Apfel",
    "sandwich": "Sandwich", "pizza": "Pizza",
    "donut": "Donut", "cake": "Kuchen",
    "orange": "Orange", "hot dog": "Hot Dog",
    "skis": "Ski", "snowboard": "Snowboard",
    "headphones": "Kopfhörer",
}


@st.cache_resource(show_spinner=False)
def load_model():
    """YOLOv8n laden — gecacht, CPU/GPU automatisch."""
    try:
        import torch
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        model.to(device)
        return model, device
    except Exception as e:
        return None, "cpu"


def detect(image: Image.Image) -> dict:
    """
    Erkennt das Hauptobjekt im Bild.
    Gibt zurück: {label, category, confidence, success}
    """
    model, device = load_model()
    if model is None:
        return {"label": "Unbekannt", "category": "Sonstiges",
                "confidence": 0.0, "success": False}

    try:
        arr = np.array(image.convert("RGB"))
        results = model(arr, verbose=False)

        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            return {"label": "Unbekanntes Objekt", "category": "Sonstiges",
                    "confidence": 0.0, "success": False}

        boxes = results[0].boxes
        confs = boxes.conf.tolist()
        cls_ids = boxes.cls.tolist()
        best = confs.index(max(confs))

        label_en = model.names[int(cls_ids[best])].lower()
        conf     = round(confs[best], 3)
        label_de = LABEL_DE.get(label_en, label_en.title())
        category = YOLO_TO_CATEGORY.get(label_en, "Sonstiges")

        return {
            "label":      label_de,
            "label_en":   label_en,
            "category":   category,
            "confidence": conf,
            "success":    True,
            "device":     device,
        }
    except Exception as e:
        return {"label": "Fehler", "category": "Sonstiges",
                "confidence": 0.0, "success": False}