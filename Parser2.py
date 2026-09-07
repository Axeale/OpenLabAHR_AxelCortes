import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

class Intent(Enum):
    PICK = "PICK"
    PLACE = "PLACE"
    MOVE = "MOVE"
    RESET = "RESET"
    UNKNOWN = "UNKNOWN"

@dataclass
class ParsedCommand:
    raw_text: str
    intent: Intent
    target: Optional[str] = None
    color: Optional[str] = None
    zone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "intent": self.intent.value,
            "target": self.target,
            "color": self.color,
            "zone": self.zone
        }


class IntentParser:
    """
    Rule-based intent parser optimized for robotics pick-and-place and navigation tasks.
    Supports English and Spanish synonyms.
    """
    def __init__(self):
        # 1. Intent Patterns (English + Spanish)
        self.intent_patterns = {
            Intent.PICK: r"\b(pick|grab|take|get|lift|agarra|toma|recoge|levanta)\b",
            Intent.PLACE: r"\b(place|put|drop|set|leave|pon|coloca|suelta|deja)\b",
            Intent.MOVE: r"\b(move|go|navigate|walk|mueve|ve|camina|desplazate)\b",
            Intent.RESET: r"\b(reset|home|init|rest|restart|inicio|reinicia|reposo)\b"
        }

        # 2. Target Objects (Normalized names)
        self.object_patterns = {
            "cube": r"\b(cube|block|box|cubo|bloque|caja)\b",
            "sphere": r"\b(sphere|ball|esfera|pelota|balon)\b",
            "cylinder": r"\b(cylinder|can|cilindro|lata)\b",
            "object": r"\b(object|item|thing|objeto|cosa)\b"
        }

        # 3. Colors
        self.color_patterns = {
            "red": r"\b(red|rojo|roja)\b",
            "green": r"\b(green|verde)\b",
            "blue": r"\b(blue|azul)\b",
            "yellow": r"\b(yellow|amarillo|amarilla)\b"
        }

        # 4. Target Spatial Zones / Locations
        self.zone_patterns = {
            "left": r"\b(left|left side|izquierda|lado izquierdo)\b",
            "right": r"\b(right|right side|derecha|lado derecho)\b",
            "center": r"\b(center|middle|centro|medio)\b",
            "table": r"\b(table|desk|mesa)\b",
            "box": r"\b(container|bin|box|caja|contenedor)\b"
        }

    def parse(self, text: str) -> ParsedCommand:
        clean_text = text.lower().strip()

        # Extract Intent
        detected_intent = Intent.UNKNOWN
        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, clean_text):
                detected_intent = intent
                break

        # Extract Target Object
        detected_target = None
        for obj_name, pattern in self.object_patterns.items():
            if re.search(pattern, clean_text):
                detected_target = obj_name
                break

        # Extract Color
        detected_color = None
        for color_name, pattern in self.color_patterns.items():
            if re.search(pattern, clean_text):
                detected_color = color_name
                break

        # Extract Spatial Zone / Target Location
        detected_zone = None
        for zone_name, pattern in self.zone_patterns.items():
            if re.search(pattern, clean_text):
                detected_zone = zone_name
                break

        return ParsedCommand(
            raw_text=text,
            intent=detected_intent,
            target=detected_target,
            color=detected_color,
            zone=detected_zone
        )


# --- Quick Demonstration / Unit Test ---
if __name__ == "__main__":
    parser = IntentParser()

    cmd = str(input("Ingresa tu prompt: "))
    result = parser.parse(cmd)
    print(f"{cmd:<40} | {result.to_dict()}")