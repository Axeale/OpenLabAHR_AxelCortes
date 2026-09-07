import re
import difflib
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

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


class FuzzyIntentParser:
    """
    Parser con tolerancia a errores ortográficos (typos)
    usando emparejamiento difuso (Fuzzy Matching).
    """
    def __init__(self, similarity_threshold: float = 0.70):
        # threshold (0.70 = 70% de similitud mínima para aceptar un typo)
        self.threshold = similarity_threshold

        # Diccionarios de palabras clave por categoría
        self.intent_keywords = {
            Intent.PICK: ["pick", "grab", "take", "lift", "agarra", "toma", "recoge", "levanta", "agarrar"],
            Intent.PLACE: ["place", "put", "drop", "set", "pon", "coloca", "suelta", "deja", "ponlo"],
            Intent.MOVE: ["move", "go", "navigate", "walk", "mueve", "ve", "camina", "desplazate"],
            Intent.RESET: ["reset", "home", "init", "restart", "inicio", "reinicia", "reposo"]
        }

        self.target_keywords = {
            "cube": ["cube", "block", "box", "cubo", "bloque", "caja"],
            "sphere": ["sphere", "ball", "esfera", "pelota", "balon"],
            "cylinder": ["cylinder", "can", "cilindro", "lata"],
            "object": ["object", "item", "thing", "objeto", "cosa"]
        }

        self.color_keywords = {
            "red": ["red", "rojo", "roja"],
            "green": ["green", "verde"],
            "blue": ["blue", "azul"],
            "yellow": ["yellow", "amarillo", "amarilla"]
        }

        self.zone_keywords = {
            "left": ["left", "izquierda", "izq"],
            "right": ["right", "derecha", "der"],
            "center": ["center", "middle", "centro", "medio"],
            "table": ["table", "desk", "mesa"]
        }


    def _find_best_match(self, tokens: List[str], mapping: dict) -> Optional[Any]:
        """Compara cada token de la frase contra la lista de palabras clave usando fuzzy matching."""
        for category, keywords in mapping.items():
            for token in tokens:
                # Busca si la palabra ingresada se parece a alguna de las palabras clave
                matches = difflib.get_close_matches(token, keywords, n=1, cutoff=self.threshold)
                if matches:
                    return category
        return None

    def parse(self, text: str) -> ParsedCommand:
        clean_text = text.lower().strip() # limpia el texto, poneindo todo el minusculas y quitando esapcios que no se ocupan
        # Extrae solo palabras, ignorando puntuación
        tokens = re.findall(r'\b\w+\b', clean_text) # el findall retorna una lista con todo lo que encontro, por eso "Tokeniza"

        # Buscar coincidencias con tolerancia a typos
        detected_intent = self._find_best_match(tokens, self.intent_keywords) or Intent.UNKNOWN
        detected_target = self._find_best_match(tokens, self.target_keywords)
        detected_color = self._find_best_match(tokens, self.color_keywords)
        detected_zone = self._find_best_match(tokens, self.zone_keywords)

        return ParsedCommand(
            raw_text=text,
            intent=detected_intent,
            target=detected_target,
            color=detected_color,
            zone=detected_zone
        )



if __name__ == "__main__":
    parser = FuzzyIntentParser(similarity_threshold=0.70)

    cmd = str(input("Ingresa el comando: "))
    result = parser.parse(cmd)
    print(f"{cmd:<35} | {result.to_dict()}")