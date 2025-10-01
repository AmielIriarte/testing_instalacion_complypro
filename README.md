# testing_instalacion_complypro

### Repositorio donde se van a subir los archivos necesarios para la instalación del aplicativo ComplyPro

## Instalación
1. Descomprimir el ZIP.
2. Ejecutar "ComplyPro.bat".
3. Ver qué pasa. Si lanza un msj de error, sacar captura. Si se cierra, revisar si se creó el archivo "update_log.txt".
4. Revisar si se instaló correctamente python poniendo "python --version" en la cmd. Debería aparecer "Python 3.11.5"

## Ejecución
### 1) ComplyPro.bat
Instala Python 3.11.5, en caso de que no lo encuentre en la máquina, y ejecuta run.bat (esto para iniciar el programa en una nueva terminal que reconozca Python).
### 2) run.bat
Crea el entorno virtual '.venv' con Python, instala las dependencias del archivo "proyecto.toml" y ejecuta "update_script.py". Una vez terminada la ejecución del script, instala las dependencias restantes del repositorio obtenido y ejecuta la aplicación de ComplyPro con streamlit.
### 3) update_script.py
Lee el token del repositorio de ComplyPro desde el .env (si está ahí) o, si no, desde la base de datos del servidor, logueándose con las credenciales que estén en el .env.
Una vez obtenido el token, usando la API de GitHub, trae el repositorio remoto (en un ZIP) en la máquina local. Descomprime este archivo y actualiza la última versión obtenida en el archivo 'last_release.txt'.
Finaliza la ejecución de este script para continuar ejecutando 'run.bat'.
