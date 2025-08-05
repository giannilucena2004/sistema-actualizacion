import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import pymysql
import threading

def abrir_ventana_actualizacion():
    nueva_ventana = tk.Toplevel()
    nueva_ventana.title("Actualizar registros")
    nueva_ventana.geometry("400x300")
    nueva_ventana.configure(bg="#ADD8E6")

    tk.Label(nueva_ventana, text="Fecha de inicio:", bg="#ADD8E6").pack(pady=5)
    entrada_inicio = DateEntry(nueva_ventana, date_pattern="yyyy-mm-dd", state="readonly")
    entrada_inicio.pack(pady=5)

    # Creamos un contenedor para guardar el resultado de la operación del hilo
    resultado_operacion = []

    def ejecutar_actualizacion_en_hilo():
        # Esta es la nueva función que contendrá la lógica de la base de datos
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

            for (
                id_empresa, agencia, tipodoc, documento, pid,
                codcliente, nombrecli, contacto, rif,
                tipoprecio, emision, vence, recepcion,
                nrocontrol, factorcamb, grupo, codigo,
                notas, estacion, baseimponible, uemisor
            ) in filas:
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

            # Guardamos el resultado del éxito
            resultado_operacion.append(("success", f"{registros_insertados} Registros actualizados\nDesde: {fecha_inicio}"))

        except Exception as e:
            # Guardamos el resultado del error
            resultado_operacion.append(("error", str(e)))

    def verificar_hilo():
        # Verificamos si el hilo ha terminado
        if hilo.is_alive():
            nueva_ventana.after(100, verificar_hilo)
        else:
            # El hilo terminó, podemos actualizar la GUI de forma segura
            progressbar.stop()
            progressbar.pack_forget()
            boton_actualizar.config(state=tk.NORMAL)
            
            # Mostramos el mensaje de éxito o error
            tipo, mensaje = resultado_operacion[0]
            if tipo == "success":
                messagebox.showinfo("Actualización", mensaje)
            else:
                messagebox.showerror("Error al actualizar", mensaje)
            
            # Vaciamos el contenedor para la próxima vez
            resultado_operacion.clear()

    def confirmar_actualizacion():
        # Desactivamos el botón para evitar múltiples clics
        boton_actualizar.config(state=tk.DISABLED)
        
        # Mostramos y arrancamos la barra de progreso
        progressbar.pack(pady=10)
        progressbar.start()

        # Creamos y ejecutamos el hilo que hará la tarea pesada
        nonlocal hilo  # Usamos el hilo que se declarará a continuación
        hilo = threading.Thread(target=ejecutar_actualizacion_en_hilo)
        hilo.start()

        # Iniciamos el chequeo periódico para ver el estado del hilo
        verificar_hilo()

    boton_actualizar = tk.Button(
        nueva_ventana, text="Actualizar", command=confirmar_actualizacion
    )
    boton_actualizar.pack(pady=20)

    progressbar = ttk.Progressbar(
        nueva_ventana,
        orient="horizontal",
        mode="indeterminate",
        length=280
    )
    
    # Declaramos el hilo para que sea accesible en las funciones anidadas
    hilo = None


# Ventana principal
ventana = tk.Tk()
ventana.geometry("600x400")
ventana.title("Sistema de actualización de registros")
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

ventana.mainloop()