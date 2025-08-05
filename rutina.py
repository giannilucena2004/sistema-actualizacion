import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import pymysql
import threading

def abrir_ventana_actualizacion():
    nueva_ventana = tk.Toplevel()
    nueva_ventana.title("Actualizar registros")
    
    # --- Lógica para centrar la ventana ---
    ancho_ventana = 400
    alto_ventana = 300
    ancho_pantalla = nueva_ventana.winfo_screenwidth()
    alto_pantalla = nueva_ventana.winfo_screenheight()
    posicion_x = int((ancho_pantalla / 2) - (ancho_ventana / 2))
    posicion_y = int((alto_pantalla / 2) - (alto_ventana / 2))
    nueva_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{posicion_x}+{posicion_y}")
    # -------------------------------------
    
    nueva_ventana.configure(bg="#ADD8E6")

    tk.Label(nueva_ventana, text="Fecha de inicio:", bg="#ADD8E6").pack(pady=5)
    entrada_inicio = DateEntry(nueva_ventana, date_pattern="yyyy-mm-dd", state="readonly")
    entrada_inicio.pack(pady=5)

    progreso_y_resultado = [0, 0, None]

    def ejecutar_actualizacion_en_hilo():
        fecha_inicio = entrada_inicio.get()
        try:
            conectar = pymysql.connect(
                host='localhost', user='root', passwd='root',
                db='adminrxdcmp', port=3306
            )
            cursor = conectar.cursor()

            cursor.execute("""
                SELECT 
                  OPERTI.id_empresa, OPERTI.agencia, OPERTI.tipodoc, OPERTI.documento, OPERMV.pid,
                  LISTVEND.cedula AS codcliente,
                  LISTVEND.nombre AS nombrecli, LISTVEND.telefonos AS contacto, LISTVEND.cedula AS rif,
                  OPERMV.tipoprecio, OPERTI.emision, OPERTI.vence, OPERTI.recepcion,
                  OPERTI.orden AS nrocontrol, OPERTI.factorreferencial AS factorcamb,
                  OPERMV.grupo, OPERMV.codigo,
                  OPERMV.nombre AS notas, OPERMV.estacion, OPERMV.mto_comi_servidor AS baseimponible,
                  OPERMV.emisor AS uemisor
                FROM OPERTI
                INNER JOIN OPERMV ON OPERTI.documento = OPERMV.documento
                INNER JOIN LISTVEND ON OPERMV.cod_servidor = LISTVEND.codigo
                WHERE OPERTI.emision >= %s
                  AND OPERTI.tipodoc = 'FAC'
                  AND OPERMV.grupo = 'HON'
            """, (fecha_inicio,))
            filas = cursor.fetchall()
            
            progreso_y_resultado[1] = len(filas)
            
            registros_insertados = 0
            insert_sql = """
                INSERT INTO gastarti (
                  id_empresa, agencia, tipodoc, documento, pid,
                  codcliente, nombrecli, contacto, rif,
                  tipoprecio, emision, vence, recepcion,
                  nrocontrol, factorcamb,
                  notas, estacion, baseimpo1, uemisor,
                  estatusdoc, totcosto, totbruto, totneto, totalfinal, totpagos
                ) VALUES (
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s,
                  %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s
                )
            """

            for i, (
                id_empresa, agencia, tipodoc, documento, pid,
                codcliente, nombrecli, contacto, rif,
                tipoprecio, emision, vence, recepcion,
                nrocontrol, factorcamb, grupo, codigo,
                notas, estacion, baseimponible, uemisor
            ) in enumerate(filas):
                
                progreso_y_resultado[0] = i + 1

                cursor.execute(
                    "SELECT 1 FROM gastarti WHERE documento = %s", (documento,)
                )
                if cursor.fetchone():
                    continue
                cursor.execute(
                    "SELECT costounit, preciounit FROM OPERMV "
                    "WHERE documento=%s AND grupo=%s AND codigo=%s",
                    (documento, grupo, codigo)
                )
                fila_prec = cursor.fetchone() or (0, 0)
                costounit, preciounit = fila_prec
                estatusdoc  = 0
                totpagos    = 0
                totcosto    = costounit
                totbruto    = preciounit
                totneto     = preciounit
                totalfinal  = preciounit
                cursor.execute(insert_sql, (
                    id_empresa, agencia, tipodoc, documento, pid,
                    codcliente, nombrecli, contacto, rif,
                    tipoprecio, emision, vence, recepcion,
                    nrocontrol, factorcamb,
                    notas, estacion, baseimponible, uemisor,
                    estatusdoc, totcosto, totbruto, totneto, totalfinal, totpagos
                ))
                registros_insertados += 1
            conectar.commit()
            cursor.close()
            conectar.close()

            if registros_insertados == 0:
                mensaje_final = f"No se encontraron registros nuevos a partir de la fecha: {fecha_inicio}"
            else:
                mensaje_final = f"{registros_insertados} Registros nuevos insertados.\nDesde la fecha: {fecha_inicio}"
            
            progreso_y_resultado[2] = ("success", mensaje_final)

        except Exception as e:
            progreso_y_resultado[2] = ("error", str(e))
    
    def verificar_hilo():
        if hilo.is_alive():
            progreso_actual, total_registros, _ = progreso_y_resultado
            
            if total_registros > 0:
                porcentaje = int((progreso_actual / total_registros) * 100)
                progressbar['value'] = porcentaje
                label_progreso.config(text=f"Actualizando {progreso_actual} de {total_registros}...")

            nueva_ventana.after(50, verificar_hilo)
        else:
            progressbar.stop()
            progressbar.pack_forget()
            label_progreso.pack_forget()
            boton_actualizar.config(state=tk.NORMAL)
            
            _, _, resultado = progreso_y_resultado
            if resultado is not None:
                tipo, mensaje = resultado
                if tipo == "success":
                    messagebox.showinfo("Actualización", mensaje)
                else:
                    messagebox.showerror("Error al actualizar", mensaje)
            
            progreso_y_resultado[0] = 0
            progreso_y_resultado[1] = 0
            progreso_y_resultado[2] = None

    def confirmar_actualizacion():
        boton_actualizar.config(state=tk.DISABLED)
        label_progreso.pack(pady=5)
        progressbar.pack(pady=5)
        
        progressbar['mode'] = 'determinate'
        progressbar['value'] = 0
        progressbar['maximum'] = 100

        nonlocal hilo
        hilo = threading.Thread(target=ejecutar_actualizacion_en_hilo)
        hilo.start()

        verificar_hilo()

    boton_actualizar = tk.Button(
        nueva_ventana, text="Actualizar", command=confirmar_actualizacion
    )
    boton_actualizar.pack(pady=20)
    
    label_progreso = tk.Label(nueva_ventana, text="", bg="#ADD8E6")

    progressbar = ttk.Progressbar(
        nueva_ventana,
        orient="horizontal",
        length=280
    )
    
    hilo = None

def mostrar_acerca_de():
    acerca_de_ventana = tk.Toplevel()
    acerca_de_ventana.title("Acerca de")
    
    # --- Lógica para centrar la ventana ---
    ancho_ventana = 430
    alto_ventana = 200
    ancho_pantalla = acerca_de_ventana.winfo_screenwidth()
    alto_pantalla = acerca_de_ventana.winfo_screenheight()
    posicion_x = int((ancho_pantalla / 2) - (ancho_ventana / 2))
    posicion_y = int((alto_pantalla / 2) - (alto_ventana / 2))
    acerca_de_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{posicion_x}+{posicion_y}")
    # -------------------------------------

    acerca_de_ventana.configure(bg="#ADD8E6")

    texto_acerca_de = (
        "Desarrollado por Gianni Lucena, Daniela Valbuena...\n"
        "Si necesitas ayuda, contáctanos en:\n"
        "ejemplo@gmail.com"
    )

    tk.Label(
        acerca_de_ventana,
        text=texto_acerca_de,
        bg="#ADD8E6",
        font=("Arial", 12),
        justify=tk.LEFT
    ).pack(padx=20, pady=20)


# Ventana principal
ventana = tk.Tk()
ventana.title("Sistema de actualización de registros")

# --- Lógica para centrar la ventana principal ---
ancho_ventana = 600
alto_ventana = 400
ancho_pantalla = ventana.winfo_screenwidth()
alto_pantalla = ventana.winfo_screenheight()
posicion_x = int((ancho_pantalla / 2) - (ancho_ventana / 2))
posicion_y = int((alto_pantalla / 2) - (alto_ventana / 2))
ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{posicion_x}+{posicion_y}")
# -------------------------------------

ventana.configure(bg="#ADD8E6")

tk.Label(
    ventana,
    text="Sistema de actualización de registros",
    bg="#ADD8E6",
    font=("Arial", 20, "bold")
).pack(pady=50)

tk.Button(
    ventana,
    text="Actualizar registros",
    command=abrir_ventana_actualizacion
).place(relx=0.5, rely=0.5, anchor="center")

tk.Button(
    ventana,
    text="Acerca de",
    command=mostrar_acerca_de
).place(relx=0.04, rely=0.95, anchor="sw")

ventana.mainloop()