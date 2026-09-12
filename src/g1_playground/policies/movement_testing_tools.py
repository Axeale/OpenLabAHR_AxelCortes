"""
Herramientas de desarrollo para calibrar y probar movimientos ANTES de
armar la secuencia completa de pick-and-place.

Ambas se implementan como Policy, para poder lanzarlas con el mismo
runner/launcher que ya usas para correr el AnkleSwingPolicy de ejemplo.
Solo cambias qué Policy le pasas al lanzador.

Contiene:
  1. JointTunerPolicy  -> para descubrir/calibrar ángulos manualmente
  2. run_phase()        -> función compartida de interpolación de una fase
  3. PhaseTestPolicy    -> para probar UNA fase aislada (ej. solo "approach")
"""

import json
import sys
import time
import threading

import numpy as np

from g1_playground.policies.policy import Policy
from g1_playground.action import JointAction, Mode
from g1_playground.state import G1State
from g1_playground.robot import (
    BODY_NUM_MOTORS,
    HAND_NUM_MOTORS,
    LEFT_HAND_SLICE,
    RIGHT_HAND_SLICE,
    G1_29DOF_NUM_MOTORS,
    VALID_NUM_MOTORS,
    G129DofJointIndex,
    G1Dex3HandJointIndex,
)


def build_joint_name_maps(has_hands: bool):
    """Arma name->indice e indice->nombre a partir de los enums reales del repo.

    Cuerpo: usa los nombres tal cual estan en G129DofJointIndex (ej. 'LeftElbow').
    Nota: algunos indices tienen dos nombres (alias), ej. LeftAnklePitch y
    LeftAnkleB son el mismo indice (4) -- ambos nombres funcionan para
    seleccionar, pero 'show'/mensajes usan el primero que aparezca (canonico).

    Manos (si has_hands=True): usa G1Dex3HandJointIndex con prefijo Left/Right,
    ej. 'LeftThumb0' -> indice 29, 'RightThumb0' -> indice 36.
    """
    name_to_idx = {}
    idx_to_name = {}
    for name, value in vars(G129DofJointIndex).items():
        if name.startswith("_"):
            continue
        name_to_idx[name] = value
        idx_to_name.setdefault(value, name)  # el primero que aparece es el "canonico"

    if has_hands:
        for name, value in vars(G1Dex3HandJointIndex).items():
            if name.startswith("_"):
                continue
            left_idx = LEFT_HAND_SLICE.start + value
            right_idx = RIGHT_HAND_SLICE.start + value
            name_to_idx[f"Left{name}"] = left_idx
            name_to_idx[f"Right{name}"] = right_idx
            idx_to_name[left_idx] = f"Left{name}"
            idx_to_name[right_idx] = f"Right{name}"

    return name_to_idx, idx_to_name


# ---------------------------------------------------------------------
# 1. TUNER: mover un motor a la vez y guardar la pose cuando te guste
# ---------------------------------------------------------------------

class JointTunerPolicy(Policy):
    """
    Controles (mientras corre, escribe en la terminal y da Enter):
      j <indice o nombre>  -> selecciona qué articulación vas a mover
      + / -                 -> incrementa/decrementa esa articulación (paso pequeño)
      show                  -> imprime el vector q actual completo
      save <nombre>         -> guarda el q actual en waypoints.json bajo ese nombre
      quit                  -> termina

    num_motors: G1_29DOF_NUM_MOTORS (29, default) para solo cuerpo/brazo,
    o el valor con manos (43) si tu UnitreeG1Robot esta configurado con Dex3.
    Debe coincidir EXACTAMENTE con el num_motors que le pasaste a tu
    UnitreeG1Robot, si no, los indices no van a corresponder.

    Los nombres de articulacion se arman SOLOS a partir de G129DofJointIndex
    (cuerpo) y G1Dex3HandJointIndex (manos, con prefijo Left/Right) -- no
    necesitas pasarlos a mano. Ejemplos validos para 'j <nombre>':
      j LeftShoulderPitch
      j RightElbow
      j LeftThumb0      (solo si num_motors incluye manos)
      j RightIndex1     (solo si num_motors incluye manos)
    """

    def __init__(self, num_motors: int = G1_29DOF_NUM_MOTORS,
                 out_file="waypoints.json", policy_dt: float = 0.02):
        if num_motors not in VALID_NUM_MOTORS:
            raise ValueError(f"num_motors invalido: {num_motors}. Debe ser uno de {VALID_NUM_MOTORS}")
        self.num_motors = num_motors
        self.has_hands = num_motors > BODY_NUM_MOTORS
        self.q = np.zeros(num_motors, dtype=np.float32)  # se llena de verdad en reset()
        self.name_to_idx, self.idx_to_name = build_joint_name_maps(self.has_hands)
        self.out_file = out_file
        self.selected = 0
        self._policy_dt = policy_dt
        self._lock = threading.Lock()
        self._start_input_thread()
        print("[tuner] articulaciones disponibles:", ", ".join(sorted(self.name_to_idx)))

    @property
    def dt(self) -> float:
        return self._policy_dt

    def reset(self, state: G1State) -> None:
        # Mismo patron que AnkleSwingPolicy: leemos la posicion REAL de
        # cada motor y la usamos como punto de partida.
        with self._lock:
            for i in range(BODY_NUM_MOTORS):
                self.q[i] = state.body.motor_state[i].q
            if self.has_hands:
                for i in range(HAND_NUM_MOTORS):
                    self.q[LEFT_HAND_SLICE][i] = state.left_hand.motor_state[i].q
                    self.q[RIGHT_HAND_SLICE][i] = state.right_hand.motor_state[i].q

    def _start_input_thread(self):
        t = threading.Thread(target=self._input_loop, daemon=True)
        t.start()

    def _input_loop(self):
        while True:
            try:
                cmd = input().strip()
            except EOFError:
                break
            with self._lock:
                self._handle_command(cmd)

    def _handle_command(self, cmd):
        if cmd.startswith("j "):
            arg = cmd.split()[1]
            if arg.isdigit():
                idx = int(arg)
                if idx >= self.num_motors:
                    print(f"[tuner] indice {idx} fuera de rango (num_motors={self.num_motors})")
                    return
                self.selected = idx
            elif arg in self.name_to_idx:
                self.selected = self.name_to_idx[arg]
            else:
                print(f"[tuner] '{arg}' no es un indice ni un nombre valido. Usa 'names' para ver la lista.")
                return
            print(f"[tuner] articulacion seleccionada: {self.selected} ({self._nombre(self.selected)})")
        elif cmd == "+":
            self.q[self.selected] += 0.05
        elif cmd == "-":
            self.q[self.selected] -= 0.05
        elif cmd == "show":
            print("[tuner] q actual:", [round(float(v), 3) for v in self.q])
        elif cmd == "names":
            print("[tuner] articulaciones disponibles:", ", ".join(sorted(self.name_to_idx)))
        elif cmd.startswith("save "):
            self._guardar(cmd.split(maxsplit=1)[1])
        elif cmd == "quit":
            sys.exit(0)
        else:
            print("[tuner] comando no reconocido:", cmd)

    def _nombre(self, idx):
        return self.idx_to_name.get(idx, f"joint_{idx}")

    def _guardar(self, nombre):
        try:
            with open(self.out_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        data[nombre] = self.q.tolist()
        with open(self.out_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[tuner] guardado waypoint '{nombre}' en {self.out_file}")

    def step(self, state: G1State) -> JointAction:
        with self._lock:
            q_actual = self.q.copy()
        return JointAction(q=q_actual, mode_pr=Mode.PR)


# ---------------------------------------------------------------------
# 2. Funcion compartida de interpolacion de fase
# ---------------------------------------------------------------------

def smoothstep(progreso):
    progreso = min(max(progreso, 0.0), 1.0)
    return progreso * progreso * (3 - 2 * progreso)


def run_phase(q_inicio, q_fin, tiempo_transcurrido, duracion):
    progreso = smoothstep(tiempo_transcurrido / duracion)
    q_inicio = np.asarray(q_inicio, dtype=np.float32)
    q_fin = np.asarray(q_fin, dtype=np.float32)
    return q_inicio + (q_fin - q_inicio) * progreso


# ---------------------------------------------------------------------
# 3. Harness para probar UNA fase aislada, en loop
# ---------------------------------------------------------------------

class PhaseTestPolicy(Policy):
    """Corre repetidamente q_inicio -> q_fin -> q_inicio, en loop."""

    def __init__(self, q_fin, num_motors: int = G1_29DOF_NUM_MOTORS,
                 duracion=2.0, pausa=1.0, policy_dt: float = 0.02):
        self.num_motors = num_motors
        self.has_hands = num_motors > BODY_NUM_MOTORS
        self.q_fin = np.asarray(q_fin, dtype=np.float32)
        self.duracion = duracion
        self.pausa = pausa
        self._policy_dt = policy_dt
        self.q_inicio = None
        self.t0 = None
        self.regresando = False

    @property
    def dt(self) -> float:
        return self._policy_dt

    def reset(self, state: G1State) -> None:
        q = np.zeros(self.num_motors, dtype=np.float32)
        for i in range(BODY_NUM_MOTORS):
            q[i] = state.body.motor_state[i].q
        if self.has_hands:
            for i in range(HAND_NUM_MOTORS):
                q[LEFT_HAND_SLICE][i] = state.left_hand.motor_state[i].q
                q[RIGHT_HAND_SLICE][i] = state.right_hand.motor_state[i].q
        self.q_inicio = q
        self.t0 = time.time()
        self.regresando = False

    def step(self, state: G1State) -> JointAction:
        t = time.time() - self.t0

        if not self.regresando:
            if t <= self.duracion:
                return JointAction(q=run_phase(self.q_inicio, self.q_fin, t, self.duracion), mode_pr=Mode.PR)
            elif t <= self.duracion + self.pausa:
                return JointAction(q=self.q_fin, mode_pr=Mode.PR)
            else:
                self.regresando = True
                self.t0 = time.time()

        t2 = time.time() - self.t0
        if t2 <= self.duracion:
            return JointAction(q=run_phase(self.q_fin, self.q_inicio, t2, self.duracion), mode_pr=Mode.PR)
        else:
            self.reset(state)  # reinicia el ciclo completo, usando el state actual
            return JointAction(q=self.q_inicio, mode_pr=Mode.PR)