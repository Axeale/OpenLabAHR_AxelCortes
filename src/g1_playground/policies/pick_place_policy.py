"""
Esqueleto de Policy para pick-and-place con el G1.
Máquina de estados: HOME -> APPROACH -> GRASP -> LIFT -> MOVE -> PLACE -> RELEASE -> HOME

Idea general:
- Cada fase tiene una pose objetivo (q) precalculada de antemano (waypoint).
- El progreso de cada fase se mide en TIEMPO REAL transcurrido, no en steps,
  para que el movimiento sea consistente sin importar la frecuencia real
  a la que te esté llamando el hilo de política.
- La policy no decide sola qué hacer: recibe comandos externos (los intents
  que ya detecta tu parser) y reacciona a ellos.
"""

import time
from enum import Enum, auto

from g1_playground.policies.policy import Policy
from g1_playground.action import JointAction, Mode


class Phase(Enum):
    IDLE = auto()       # esperando comando
    APPROACH = auto()   # acercando la mano al objeto
    GRASP = auto()       # cerrando la mano/pinza
    LIFT = auto()        # levantando el objeto
    MOVE = auto()         # moviendo el brazo hacia la zona destino
    PLACE = auto()        # bajando sobre la zona destino
    RELEASE = auto()      # abriendo la mano
    HOME = auto()          # regresando a pose neutral


# Duración objetivo de cada fase, en segundos. Ajusta según se vea en sim.
PHASE_DURATIONS = {
    Phase.APPROACH: 2.0,
    Phase.GRASP: 1.0,
    Phase.LIFT: 1.5,
    Phase.MOVE: 2.5,
    Phase.PLACE: 1.5,
    Phase.RELEASE: 1.0,
    Phase.HOME: 2.0,
}


def lerp(q_inicio, q_fin, progreso):
    """Interpolación lineal simple entre dos vectores de ángulos."""
    progreso = min(max(progreso, 0.0), 1.0)  # clamp por seguridad
    return [a + (b - a) * progreso for a, b in zip(q_inicio, q_fin)]


class PickPlacePolicy(Policy):

    def __init__(self, waypoints: dict):
        """
        waypoints: dict con los q "hardcodeados" que ya midieron a mano,
        ej: {"home": [...], "approach_cube": [...], "grasp_cube": [...], ...}
        """
        self.waypoints = waypoints
        self.phase = Phase.IDLE
        self.phase_start_time = None
        self.q_phase_start = None   # pose desde donde arrancó esta fase
        self.q_phase_target = None  # pose a la que va esta fase
        self.pending_command = None  # aquí llega el intent del parser

    def reset(self):
        self.phase = Phase.IDLE
        self.phase_start_time = None

    def set_command(self, intent: str, target_object: str = None, target_zone: str = None):
        """Llamas esto desde afuera cuando tu parser detecta un intent nuevo."""
        self.pending_command = {
            "intent": intent,
            "object": target_object,
            "zone": target_zone,
        }

    def _start_phase(self, phase: Phase, current_q):
        self.phase = phase
        self.phase_start_time = time.time()
        self.q_phase_start = current_q
        self.q_phase_target = self._target_for_phase(phase)

    def _target_for_phase(self, phase: Phase):
        # Aquí conectas cada fase con el waypoint correspondiente.
        # Simplificado a un solo objeto/zona; puedes parametrizarlo por
        # target_object / target_zone si tienes varias escenas.
        mapping = {
            Phase.APPROACH: self.waypoints["approach_cube"],
            Phase.GRASP: self.waypoints["grasp_cube"],
            Phase.LIFT: self.waypoints["lift"],
            Phase.MOVE: self.waypoints["move_zone"],
            Phase.PLACE: self.waypoints["place_zone"],
            Phase.RELEASE: self.waypoints["release"],
            Phase.HOME: self.waypoints["home"],
        }
        return mapping[phase]

    def step(self, state):
        current_q = state.body_q  # ajusta al nombre real del campo en G1State

        # 1. Si estamos IDLE y llegó un comando nuevo, arrancamos la secuencia
        if self.phase == Phase.IDLE and self.pending_command is not None:
            self._start_phase(Phase.APPROACH, current_q)
            self.pending_command = None

        # 2. Si estamos IDLE sin comando, nos quedamos quietos en home
        if self.phase == Phase.IDLE:
            return JointAction(q=self.waypoints["home"], mode_pr=Mode.PR)

        # 3. Calculamos progreso de la fase actual en TIEMPO real
        duracion = PHASE_DURATIONS[self.phase]
        transcurrido = time.time() - self.phase_start_time
        progreso = transcurrido / duracion

        q_objetivo = lerp(self.q_phase_start, self.q_phase_target, progreso)

        # 4. Si terminamos esta fase, pasamos a la siguiente
        if progreso >= 1.0:
            siguiente = self._siguiente_fase(self.phase)
            if siguiente is not None:
                self._start_phase(siguiente, self.q_phase_target)
            else:
                self.phase = Phase.IDLE  # secuencia completa

        return JointAction(q=q_objetivo, mode_pr=Mode.PR)

    def _siguiente_fase(self, fase_actual: Phase):
        orden = [Phase.APPROACH, Phase.GRASP, Phase.LIFT,
                 Phase.MOVE, Phase.PLACE, Phase.RELEASE, Phase.HOME]
        idx = orden.index(fase_actual)
        if idx + 1 < len(orden):
            return orden[idx + 1]
        return None  # ya terminó todo, regresa a IDLE
