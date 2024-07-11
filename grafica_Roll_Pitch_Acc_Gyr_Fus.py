import serial
import re
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from threading import Thread
import time
from datetime import datetime

# Configuración del puerto serie
port = 'COM3'
baudrate = 230400
ser = serial.Serial(port, baudrate)

# Listas de datos
max_points = 1000  # Ventana de visualización en tiempo real
samples = []

# Datos de Pitch
ACC_pitch_data = []
GYR_pitch_data = []
FUS_pitch_data = []

# Datos de Roll
ACC_roll_data = []
GYR_roll_data = []
FUS_roll_data = []

# Función para extraer los valores del puerto serie
def extract_values(data):
    pattern_pitch = re.compile(r'ACC_pitch: ([\-\d.]+) , GYR_pitch: ([\-\d.]+) , pitch: ([\-\d.]+)')
    pattern_roll = re.compile(r'ACC_roll: ([\-\d.]+) , GYR_roll: ([\-\d.]+) , roll: ([\-\d.]+)')
    match_pitch = pattern_pitch.match(data)
    match_roll = pattern_roll.match(data)
    if match_pitch:
        ACC_pitch = float(match_pitch.group(1))
        GYR_pitch = float(match_pitch.group(2))
        FUS_pitch = float(match_pitch.group(3))
        return 'pitch', ACC_pitch, GYR_pitch, FUS_pitch
    elif match_roll:
        ACC_roll = float(match_roll.group(1))
        GYR_roll = float(match_roll.group(2))
        FUS_roll = float(match_roll.group(3))
        return 'roll', ACC_roll, GYR_roll, FUS_roll
    print(f"No match for data: {data}")  # Mensaje de depuración
    return None, None, None, None

# Función para leer datos del puerto serie
def read_serial():
    global running
    running = True
    while running:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            #print(f"Received data: {data}")  # Mensaje de depuración
            if data == "FIN":
                print("Recibido FIN. Deteniendo el programa.")
                running = False  # Detiene el bucle
                break
            type_, val1, val2, val3 = extract_values(data)
            if type_ == 'pitch':
                ACC_pitch_data.append(val1)
                GYR_pitch_data.append(val2)
                FUS_pitch_data.append(val3)
                samples.append(len(samples) + 1)
            elif type_ == 'roll':
                ACC_roll_data.append(val1)
                GYR_roll_data.append(val2)
                FUS_roll_data.append(val3)
                if len(samples) < len(ACC_roll_data):
                    samples.append(len(samples) + 1)
        time.sleep(0.01)  # Pausa para no saturar la CPU

# Iniciar el hilo de lectura del puerto serie
serial_thread = Thread(target=read_serial)
serial_thread.start()

# Crear la aplicación Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Gráficas en Tiempo Real de Datos del Puerto Serie'),
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=100,  # Intervalo en milisegundos (1s)
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=('Gráfica de Pitch', 'Gráfica de Roll'))

    if samples:
        # Gráfica de Pitch
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=ACC_pitch_data[-max_points:], mode='lines', name='ACC Pitch'), row=1, col=1)
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=GYR_pitch_data[-max_points:], mode='lines', name='GYR Pitch'), row=1, col=1)
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=FUS_pitch_data[-max_points:], mode='lines', name='FUS Pitch'), row=1, col=1)

        # Gráfica de Roll
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=ACC_roll_data[-max_points:], mode='lines', name='ACC Roll'), row=2, col=1)
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=GYR_roll_data[-max_points:], mode='lines', name='GYR Roll'), row=2, col=1)
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=FUS_roll_data[-max_points:], mode='lines', name='FUS Roll'), row=2, col=1)

    fig.update_layout(title_text='Gráficas de Pitch y Roll en Tiempo Real', height=800)
    fig.update_xaxes(title_text='Número de muestras')
    fig.update_yaxes(title_text='Pitch (grados)', row=1, col=1)
    fig.update_yaxes(title_text='Roll (grados)', row=2, col=1)

    return fig

# Ejecutar la aplicación Dash
if __name__ == '__main__':
    try:
        app.run_server(debug=True, use_reloader=False)
    finally:
        running = False
        ser.close()
        serial_thread.join()
        print(f"Conexión con {port} cerrada.")

        # Crear las gráficas interactivas finales
        final_fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  subplot_titles=('Gráfica de Pitch', 'Gráfica de Roll'))

        if samples:
            # Gráfica de Pitch
            final_fig.add_trace(go.Scatter(x=samples, y=ACC_pitch_data, mode='lines', name='ACC Pitch'), row=1, col=1)
            final_fig.add_trace(go.Scatter(x=samples, y=GYR_pitch_data, mode='lines', name='GYR Pitch'), row=1, col=1)
            final_fig.add_trace(go.Scatter(x=samples, y=FUS_pitch_data, mode='lines', name='FUS Pitch'), row=1, col=1)

            # Gráfica de Roll
            final_fig.add_trace(go.Scatter(x=samples, y=ACC_roll_data, mode='lines', name='ACC Roll'), row=2, col=1)
            final_fig.add_trace(go.Scatter(x=samples, y=GYR_roll_data, mode='lines', name='GYR Roll'), row=2, col=1)
            final_fig.add_trace(go.Scatter(x=samples, y=FUS_roll_data, mode='lines', name='FUS Roll'), row=2, col=1)

        final_fig.update_layout(title_text='Gráficas de Pitch y Roll', height=800)
        final_fig.update_xaxes(title_text='Número de muestras')
        final_fig.update_yaxes(title_text='Pitch (grados)', row=1, col=1)
        final_fig.update_yaxes(title_text='Roll (grados)', row=2, col=1)

        # Guardar las gráficas interactivas como un archivo HTML
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'grafica_interactiva_{now}.html'
        final_fig.write_html(output_file)
        print(f"Gráficas interactivas guardadas como '{output_file}'.")
