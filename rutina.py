import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import pymysql

def abrir_ventana_actualizacion():
    nueva_ventana = tk.Toplevel()
    nueva_ventana.title("Actualizar registros")
    nueva_ventana.geometry("400x300")
    nueva_ventana.configure(bg="#ADD8E6")

    tk.Label(nueva_ventana, text="Fecha de inicio:", bg="#ADD8E6").pack(pady=5)
    entrada_inicio = DateEntry(nueva_ventana, date_pattern="yyyy-mm-dd", state="readonly")
    entrada_inicio.pack(pady=5)


    def confirmar_actualizacion():
        fecha_inicio = entrada_inicio.get()

        try:
            conectar = pymysql.connect(
                host='localhost', user='root', passwd='root',
                db='adminrxdcmp', port=3306
            )
            cursor = conectar.cursor()

            # 1) Traemos 20 columnas incluyendo grupo y código
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
            """, (fecha_inicio))
            filas = cursor.fetchall()

            registros_insertados = 0

            # 2) Plantilla INSERT en gastarti
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

            # --- NUEVA VERIFICACIÓN DE EXISTENCIA DEL REGISTRO ---
                cursor.execute(
                    "SELECT 1 FROM gastarti WHERE documento = %s", (documento,)
                )
                if cursor.fetchone():
                    # El registro ya existe, lo saltamos
                    continue
                # --- FIN DE LA VERIFICACIÓN ---

                # 3) Recuperar precio/costo unitario filtrando también por grupo y código
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

            # 4) Commit una sola vez
            conectar.commit()
            cursor.close()
            conectar.close()

            messagebox.showinfo(
                "Actualización",
                f"{registros_insertados} Registros actualizados\n"
                f"Desde: {fecha_inicio}"
            )

        except Exception as e:
            messagebox.showerror("Error al actualizar", str(e))

    tk.Button(
        nueva_ventana, text="Actualizar", command=confirmar_actualizacion
    ).pack(pady=20)

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
