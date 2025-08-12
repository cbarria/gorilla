## Gorilla (QBASIC-style) in Pygame

Un clon simple del clásico Gorilla de QBasic, hecho con Pygame. Multijugador local por turnos, control por teclado, con viento, ángulo y potencia.

### Requisitos

- Python 3.9+
- Pygame (se instala con `requirements.txt`)

### Instalación (Windows PowerShell)

```powershell
cd .\gorilla
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Ejecución

```powershell
python .\src\gorilla.py
```

### Cómo jugar

- Dos jugadores se turnan para lanzar un plátano entre edificios.
- Se ingresa primero el ángulo (0–180) y luego la potencia (1–100). Confirmar con Enter.
- El viento afecta la trayectoria. Mira la flecha y el valor en la parte superior.
- Gana quien acierte al gorila contrario. Presiona `R` para reiniciar ronda, `Esc` para salir.

### Controles

- Ingresar números con el teclado, `Backspace` para borrar, `Enter` para confirmar.
- `R`: reiniciar cuando la ronda termina.
- `Esc`: salir.

### Notas

- El terreno es destructible visualmente y en colisión alrededor de la explosión.
- Código pensado para ser claro y educativo, no optimizado.


