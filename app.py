#libreria para datos
import pandas as pd
import numpy as np
#librerias para pdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
#librerias para app web
import streamlit as st
#libreria para leer documentos
import os
import shutil
from openpyxl import load_workbook
#libreria para tiempo
import time
from datetime import datetime


#img = Image.open("Calculadora.jpg")

st.set_page_config(
    page_title="Análisis de Saturación de CTs",
    #page_icon=img,
    #layout="centered",
    layout="wide",
    initial_sidebar_state="collapsed"
)


#declaracion de funciones
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#leer excel con datos de mantenimiento
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def leer_excel_pandas():

    base_dir = os.path.dirname(__file__)

    ruta_excel = os.path.join(base_dir, "data", "looker.xlsx")

    df = pd.read_excel(ruta_excel, sheet_name=0)

    return df

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def GuardarPdf():
    """
    Prepara el directorio de salida para el reporte PDF:
    - Crea la carpeta si no existe
    - Limpia su contenido si ya existe
    - Genera una ruta de salida con timestamp
    """

    # =========================
    # 1. Directorio base
    # =========================
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, "outputs_Mantenimiento")

    # =========================
    # 2. Verificar / crear / limpiar carpeta
    # =========================
    if os.path.exists(output_dir):
        # Elimina todo el contenido previo
        for archivo in os.listdir(output_dir):
            ruta_archivo = os.path.join(output_dir, archivo)
            try:
                if os.path.isfile(ruta_archivo):
                    os.remove(ruta_archivo)
                elif os.path.isdir(ruta_archivo):
                    shutil.rmtree(ruta_archivo)
            except Exception as e:
                print(f"No se pudo eliminar {ruta_archivo}: {e}")
    else:
        os.makedirs(output_dir)

    # =========================
    # 3. Generar nombre con timestamp
    # =========================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_pdf = f"Reporte_Mantenimiento_{timestamp}.pdf"

    ruta_salida = os.path.join(output_dir, nombre_pdf)

    return ruta_salida

#leer dataframe en cierto intervalo de tiempo estipulado por el usuario
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def FiltroExcelFechas(df, fecha_min, fecha_max):

    df = df.copy() # Evita modificar el DataFrame original fuera de la función
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce") #Convierte la columna "fecha" a tipo datetime64[ns]: datetime/ NaT
    df = df.dropna(subset=["fecha"]) #Eliminación de fechas inválidas

    fecha_min = pd.to_datetime(fecha_min) #Convierte las fechas seleccionadas por el usuario a Timestamp
    fecha_max = pd.to_datetime(fecha_max) #Convierte las fechas seleccionadas por el usuario a Timestamp

    
    df_filtrado = df[(df["fecha"] >= fecha_min) & (df["fecha"] <= fecha_max)] #Filtrado por rango de fechas]

    return df_filtrado


def RespuestosCriticos(df, fechamin, fechamax):
    """
    Retorna los 20 puestos más críticos en un rango de fechas,
    definidos como los puestos con mayor número de registros.
    """

    # Copia para no modificar el DataFrame original
    df = df.copy()

    # Conversión y limpieza de fechas
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    fechamin = pd.to_datetime(fechamin)
    fechamax = pd.to_datetime(fechamax)

    # Filtrado por rango de fechas
    df = df[(df["fecha"] >= fechamin) & (df["fecha"] <= fechamax)]

    # Validación
    if df.empty:
        return {
            "mensaje": "No existen registros en el rango de fechas seleccionado."
        }

    # Conteo de puestos (criticidad)
    puestos_criticos = (
        df["puesto"]
        .value_counts()        # Conteo por puesto
        .sort_values(ascending=False)
        .head(20)              # Top 20
    )

    # Construcción del reporte
    reporte1 = {
        "fecha_min": fechamin.strftime("%d/%m/%Y"),
        "fecha_max": fechamax.strftime("%d/%m/%Y"),
        "total_registros": int(len(df)),
        "top_20_puestos_criticos": puestos_criticos.to_dict()
    }

    return reporte1



#Filtrar el analisis por Maquina
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def FiltroExcelMaquinas(df_filtrado, PuestoUsuario):
    """
    Genera un reporte técnico de mantenimiento para un puesto específico,
    a partir de un DataFrame previamente cargado.
    """

    # =========================
    # 1. Normalización inicial
    # =========================
    df = df_filtrado.copy()

    # Limpieza básica de strings
    df["puesto"] = df["puesto"].astype(int) #astype(str).str.strip()
    df["maquina"] = df["maquina"].astype(str).str.strip()
    df["averia"] = df["averia"].astype(str).str.strip()
    df["mecanico"] = df["mecanico"].astype(str).str.strip()
    df["repuesto"] = df["repuesto"].astype(str).str.strip()

    # Conversión de fechas
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    # =========================
    # 2. Filtro por puesto
    # =========================
    df = df[df["puesto"] == PuestoUsuario]

    # Validación post-filtro
    if df.empty:
        return {
            "puesto_analizado": PuestoUsuario,
            "mensaje": "No existen registros para el puesto seleccionado."
        }
    

    # =========================
    # 3. Inicialización reporte
    # =========================
    reporte = {}

    # =========================
    # 4. Resumen general
    # =========================
    total_registros = len(df)
    fecha_min_dt = df["fecha"].min()
    fecha_max_dt = df["fecha"].max()

    mecanicos = df["mecanico"].value_counts()

    reporte["resumen_general"] = {
        "puesto_analizado": PuestoUsuario,
        "total_registros": total_registros,
        "fecha_minima": fecha_min_dt.strftime("%d/%m/%Y"),
        "fecha_maxima": fecha_max_dt.strftime("%d/%m/%Y"),
        "tecnico_principal": mecanicos.idxmax(),
        "cantidad_trabajos_tecnico_principal": int(mecanicos.max()),
        "dias_analizados": int((fecha_max_dt - fecha_min_dt).days + 1)
    }

    # =========================
    # 5. Análisis descriptivo
    # =========================
    reporte["fallas_frecuentes"] = df["averia"].value_counts().to_dict()
    reporte["maquinas_criticas"] = df["maquina"].value_counts().to_dict()
    reporte["repuestos_frecuentes"] = df["repuesto"].value_counts().to_dict()

    # =========================
    # 6. Detalle por avería
    # =========================
    reporte["detalle_por_averia"] = (
        df.groupby("averia")
          .agg(
              total_fallas=("maquina", "count"),
              maquinas_afectadas=("maquina", lambda x: list(x.unique())),
              repuestos_asociados=("repuesto", lambda x: list(x.unique()))
          )
          .sort_values("total_fallas", ascending=False)
          .to_dict(orient="index")
    )

    # =========================
    # 7. Análisis por máquina
    # =========================
    analisis_maquina = (
        df.groupby("maquina")
          .agg(
              total_fallas=("averia", "count"),
              tipos_falla=("averia", "nunique"),
              falla_principal=("averia", lambda x: x.value_counts().idxmax()),
              tecnico_principal=("mecanico", lambda x: x.value_counts().idxmax()),
              repuesto_principal=("repuesto", lambda x: x.value_counts().idxmax())
          )
    )

    reporte["analisis_por_maquina"] = analisis_maquina.to_dict(orient="index")

    # =========================
    # 8. Intensidad de fallas
    # =========================
    dias_periodo = (fecha_max_dt - fecha_min_dt).days + 1

    reporte["intensidad_fallas_maquina"] = (
        analisis_maquina["total_fallas"]
        .apply(lambda x: round(x / dias_periodo, 3))
        .sort_values(ascending=False)
        .to_dict()
    )

    # =========================
    # 9. Tendencia temporal
    # =========================
    reporte["fallas_por_dia"] = (
        df.groupby(df["fecha"].dt.date)
          .size()
          .to_dict()
    )

    # =========================
    # 10. Relación máquina-repuesto
    # =========================
    reporte["relacion_maquina_repuesto"] = (
        df.groupby(["maquina", "repuesto"])
          .size()
          .sort_values(ascending=False)
          .to_dict()
    )

    # =========================
    # 11. Especialización técnica
    # =========================
    reporte["especializacion_tecnica"] = (
        df.groupby(["mecanico", "averia"])
          .size()
          .sort_values(ascending=False)
          .to_dict()
    )

    # =========================
    # 12. Índice de criticidad
    # =========================
    criticidad = analisis_maquina.copy()
    criticidad["indice_criticidad"] = (
        criticidad["total_fallas"] * criticidad["tipos_falla"]
    )

    reporte["indice_criticidad_maquina"] = (
        criticidad["indice_criticidad"]
        .sort_values(ascending=False)
        .to_dict()
    )

    return reporte


def _crear_tabla(data):
    """
    Crea una tabla ReportLab con estilo estándar.
    """
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _tabla_diccionario(diccionario, encabezados):
    """
    Convierte un diccionario simple en tabla PDF.
    """
    data = [encabezados] + [[k, v] for k, v in diccionario.items()]
    return _crear_tabla(data)



def generar_pdf_reporte(reporte, ruta_pdf):
    """
    Genera un PDF técnico a partir del diccionario de reporte
    producido por FiltroExcelMaquinas.
    """

    # =========================
    # 1. Documento base
    # =========================
    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    titulo = Paragraph(
        "<b>REPORTE TÉCNICO DE MANTENIMIENTO</b>",
        styles["Title"]
    )
    story.append(titulo)
    story.append(Spacer(1, 20))

    # =========================
    # 2. Resumen general
    # =========================
    story.append(Paragraph("<b>1. Resumen General</b>", styles["Heading2"]))
    resumen = reporte["resumen_general"]

    tabla_resumen = [
        ["Puesto analizado", resumen["puesto_analizado"]],
        ["Total de registros", resumen["total_registros"]],
        ["Periodo analizado", f'{resumen["fecha_minima"]} – {resumen["fecha_maxima"]}'],
        ["Días analizados", resumen["dias_analizados"]],
        ["Técnico principal", resumen["tecnico_principal"]],
        ["Trabajos técnico principal", resumen["cantidad_trabajos_tecnico_principal"]],
    ]

    story.append(_crear_tabla(tabla_resumen))
    story.append(Spacer(1, 16))

    # =========================
    # 3. Fallas más frecuentes
    # =========================
    story.append(Paragraph("<b>2. Fallas más frecuentes</b>", styles["Heading2"]))

    story.append(_tabla_diccionario(
        reporte["fallas_frecuentes"],
        ["Avería", "Cantidad"]
    ))

    # =========================
    # 4. Máquinas críticas
    # =========================
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>3. Máquinas más críticas</b>", styles["Heading2"]))

    story.append(_tabla_diccionario(
        reporte["maquinas_criticas"],
        ["Máquina", "Total de fallas"]
    ))

    # =========================
    # 5. Índice de criticidad
    # =========================
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>4. Índice de criticidad por máquina</b>", styles["Heading2"]))

    story.append(_tabla_diccionario(
        reporte["indice_criticidad_maquina"],
        ["Máquina", "Índice de criticidad"]
    ))

    # =========================
    # 6. Análisis por máquina
    # =========================
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>5. Análisis detallado por máquina</b>", styles["Heading2"]))

    for maquina, datos in reporte["analisis_por_maquina"].items():
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Máquina:</b> {maquina}", styles["Normal"]))

        tabla_maquina = [
            ["Total de fallas", datos["total_fallas"]],
            ["Tipos de falla", datos["tipos_falla"]],
            ["Falla principal", datos["falla_principal"]],
            ["Técnico principal", datos["tecnico_principal"]],
            ["Repuesto principal", datos["repuesto_principal"]],
        ]

        story.append(_crear_tabla(tabla_maquina))

    # =========================
    # 7. Construcción del PDF
    # =========================
    doc.build(story)




def main():

        # =====================================================================
        # # INTERFAZ STREAMLIT
        # # =====================================================================

        st.markdown("""
        <div style="padding:20px; background:#0E1117; border-radius:12px; border:1px solid #1f2937;
                    box-shadow:0 6px 12px rgba(0,0,0,0.35); margin-bottom:25px;">
            <h1 style="margin:0; color:white;">⚙️ Reporte General de Mantenimientos</h1>
            <p style="color:#9CA3AF; margin-top:6px;">Sistema elaborado por los Ingenieros: Daniel Cano y Santiago Cano</p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡Este módulo permite analizar los registros históricos de mantenimiento, " 
                "identificando fallas recurrentes, equipos críticos y tendencias operativas "
                "a partir de un rango de fechas y un puesto específico.")
        
        # --------------------------------------------------
        # 1. Cargar datos
        # --------------------------------------------------
        df = leer_excel_pandas()
        # Asegurar tipo fecha
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"])

        # --------------------------------------------------
        # # 2. Rango de fechas real del Excel
        # # --------------------------------------------------}

        fecha_min_excel = df["fecha"].min().date()
        fecha_max_excel = df["fecha"].max().date()

        # --------------------------------------------------
        # # 3. Sidebar / Panel de filtros
        # # --------------------------------------------------
        st.sidebar.header("Filtros de análisis")
        
        fecha_seleccionada = st.sidebar.date_input(
            "Seleccione el rango de fechas",
            value=(fecha_min_excel, fecha_max_excel),
            min_value=fecha_min_excel,
            max_value=fecha_max_excel
            )
        # Validación segura
        if not isinstance(fecha_seleccionada, tuple):
            st.warning("Seleccione un rango de fechas válido.")
            st.stop()

        fecha_inicio, fecha_fin = fecha_seleccionada

        if fecha_inicio > fecha_fin:
            st.error("La fecha inicial no puede ser mayor que la fecha final.")
            st.stop()
            # Normalización para pandas
            #fecha_inicio = pd.Timestamp(fecha_inicio)
            #fecha_fin = pd.Timestamp(fecha_fin)

        
        # --------------------------------------------------
        # # 4. Selector de puesto
        # # --------------------------------------------------
        puestos_disponibles = sorted(df["puesto"].astype(int).unique())
        puesto_min = puestos_disponibles[0]
        puesto_max = puestos_disponibles[-1]
        puesto_seleccionado = st.sidebar.selectbox(f"Seleccione el puesto (entre {puesto_min} y {puesto_max})",puestos_disponibles)

        # --------------------------------------------------
        # 5. Botón de ejecución
        # # --------------------------------------------------

        if st.sidebar.button("Generar reporte"):

            df_filtrado = FiltroExcelFechas(df, fecha_inicio, fecha_fin)

            reporte = FiltroExcelMaquinas(df_filtrado, puesto_seleccionado)
            if "resumen_general" not in reporte:
                st.warning(reporte.get("mensaje", "No hay datos para generar el reporte."))
            else:
                ruta_pdf = GuardarPdf()
                generar_pdf_reporte(reporte, ruta_pdf)

                st.success("📄 Reporte PDF generado correctamente")

                # -------------------------------
                # # DESCARGA DEL PDF
                # # -------------------------------

                with open(ruta_pdf, "rb") as pdf_file:
                    st.download_button(
                    label="⬇️ Descargar reporte PDF",
                    data=pdf_file,
                    file_name=os.path.basename(ruta_pdf),
                    mime="application/pdf")



            #reporte = FiltroExcelMaquinas(df_filtrado, puesto_seleccionado)
            #ruta_pdf = GuardarPdf()
            #generar_pdf_reporte(reporte, ruta_pdf)

        # --------------------------------------------------
        # # 6. Mostrar Top 20 Puestos Críticos
        # # --------------------------------------------------
        
        st.subheader("📊 Top 20 Puestos más Críticos")
        reporte_puestos = RespuestosCriticos(df, fecha_inicio, fecha_fin)
        # Validación
        if "mensaje" in reporte_puestos:
            st.warning(reporte_puestos["mensaje"])
        else:
            # Resumen
            st.markdown(f"""
                        **Período analizado:** {reporte_puestos['fecha_min']} – {reporte_puestos['fecha_max']}  
                        **Total de registros:** {reporte_puestos['total_registros']}""")
            
            # Convertir a DataFrame para visualización
            df_puestos_criticos = (
            pd.DataFrame(
            reporte_puestos["top_20_puestos_criticos"].items(),
            columns=["Puesto", "Cantidad de eventos"])
            .sort_values("Cantidad de eventos", ascending=False)
            .reset_index(drop=True))
            
           
            
            st.metric(
                label="Puesto más crítico",
                value=df_puestos_criticos.iloc[0]["Puesto"],
                delta=f'{df_puestos_criticos.iloc[0]["Cantidad de eventos"]} eventos'
                )
            
            st.bar_chart(df_puestos_criticos.set_index("Puesto"))

             # Mostrar tabla
            st.dataframe(
                df_puestos_criticos,
                use_container_width=True)


    

# ---------- EJECUCIÓN ----------
if __name__ == "__main__":
    main()






















    













