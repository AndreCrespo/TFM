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
port = 'COM5'
baudrate = 460800
ser = serial.Serial(port, baudrate)

# Listas de datos
max_points = 1000  # Ventana de visualización en tiempo real
samples = []

# Datos del ángulo de perturbación y posición del motor
IMU_data = []
Real_Pos_data = []

# Función para extraer los valores del puerto serie
def extract_values(data):
    pattern = re.compile(r'IMU: ([\-\d.]+) , Real Pos: ([\-\d.]+)')
    match = pattern.match(data)
    if match:
        IMU = float(match.group(1))
        Real_Pos = float(match.group(2))
        return IMU, Real_Pos
    print(f"No match for data: {data}")  # Mensaje de depuración
    return None, None

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
            IMU, Real_Pos = extract_values(data)
            if IMU is not None and Real_Pos is not None:
                IMU_data.append(IMU)
                Real_Pos_data.append(Real_Pos)
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
        interval=100,  # Intervalo en milisegundos (0.1s)
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=('Ángulo de Perturbación y Posición del Motor', 'Diferencia Absoluta'))

    if samples:
        # Gráfica de Ángulo de Perturbación y Posición del Motor
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=IMU_data[-max_points:], mode='lines', name='Ángulo de Perturbación (IMU)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=Real_Pos_data[-max_points:], mode='lines', name='Posición del Motor (Encoder)'), row=1, col=1)

        # Calcular la diferencia absoluta
        diff_data = [abs(imu - real) for imu, real in zip(IMU_data[-max_points:], Real_Pos_data[-max_points:])]

        # Gráfica de Diferencia Absoluta
        fig.add_trace(go.Scatter(x=samples[-max_points:], y=diff_data, mode='lines', name='Diferencia Absoluta'), row=2, col=1)

    fig.update_layout(title_text='Ángulo de Perturbación y Posición del Motor en Tiempo Real', height=800)
    fig.update_xaxes(title_text='Número de muestras')
    fig.update_yaxes(title_text='Ángulo / Posición (grados)', row=1, col=1)
    fig.update_yaxes(title_text='Diferencia Absoluta (grados)', row=2, col=1)

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
                                  subplot_titles=('Ángulo de Perturbación y Posición del Motor', 'Diferencia Absoluta'))

        if samples:
            # Gráfica de Ángulo de Perturbación y Posición del Motor
            final_fig.add_trace(go.Scatter(x=samples, y=IMU_data, mode='lines', name='Ángulo de Perturbación (IMU)'), row=1, col=1)
            final_fig.add_trace(go.Scatter(x=samples, y=Real_Pos_data, mode='lines', name='Posición del Motor (Real Pos)'), row=1, col=1)

            # Calcular la diferencia absoluta
            diff_data = [(imu - real)/3 for imu, real in zip(IMU_data, Real_Pos_data)]

            # Gráfica de Diferencia Absoluta
            final_fig.add_trace(go.Scatter(x=samples, y=diff_data, mode='lines', name='Diferencia Absoluta'), row=2, col=1)

        final_fig.update_layout(title_text='Ángulo de Perturbación y Posición del Motor', height=800)
        final_fig.update_xaxes(title_text='Número de muestras')
        final_fig.update_yaxes(title_text='Ángulo / Posición (grados)', row=1, col=1)
        final_fig.update_yaxes(title_text='Diferencia Absoluta (grados)', row=2, col=1)

        # Guardar las gráficas interactivas como un archivo HTML
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'grafica_interactiva_{now}.html'
        final_fig.write_html(output_file)
        print(f"Gráficas interactivas guardadas como '{output_file}'.")
