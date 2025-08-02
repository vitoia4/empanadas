import flet as ft

def main(page: ft.Page):
    # --- Configuración inicial de ventana ---
    if hasattr(page, "window"):
        page.window.width = 450
        page.window.height = 640
    page.title = "Contador de Empanadas"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    page.spacing = 20

    # --- Variables principales ---
    sabores, conteos, personas = [], {}, {}
    objetivo_empanadas, objetivo_personas = 0, 0
    textos, textos_persona = {}, {}
    mostrar_por_personas = True
    tipo_conteo_elegido = None
    ya_pregunto_empanadas = False
    ya_pregunto_personas = False


    # --- Lista de sabores sugeridos ---
    sabores_sugeridos = ["Jamón y queso", "Carne S", "Carne P", "Carne Cuchillo", "Capresse", "Pollo", "Verdura", "Humita"]

    # --- Widgets para la pantalla inicial ---
    sabor_input = ft.TextField(label="Agregar sabor de empanada", width=250)
    btn_agregar = ft.ElevatedButton("Agregar sabor", disabled=True)
    sabores_list = ft.ListView(spacing=5, padding=5, height=150, width=400)
    btn_confirmar_sabores = ft.ElevatedButton("Confirmar sabores", on_click=lambda e: mostrar_opcion_tipo_conteo(), disabled=True)

    # --- Funciones auxiliares para la pantalla inicial ---
    def actualizar_agregar(e=None):
        btn_agregar.disabled = not (sabor_input.value or "").strip()
        page.update()

    def agregar_sabor_manual(e):
        agregar_sabor(sabor_input.value)
        sabor_input.value = ""
        btn_agregar.disabled = True
        page.update()

    def check_sabores(e=None):
        btn_confirmar_sabores.disabled = len(sabores) == 0
        page.update()

    # --- Manejo de sabores ---
    def mostrar_sabores():
        sabores_list.controls.clear()
        for s in sabores:
            sabores_list.controls.append(
                ft.Row([
                    ft.Text(s, size=18),
                    ft.IconButton(icon="close", icon_color="red", tooltip="Eliminar sabor",
                                  on_click=lambda e, sabor=s: eliminar_sabor(sabor))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
            )
        page.update()

    def eliminar_sabor(sabor):
        if sabor in sabores:
            sabores.remove(sabor)
            conteos.pop(sabor, None)
            textos.pop(sabor, None)
            textos_persona.pop(sabor, None)

            # Eliminar el sabor de cada persona y borrar personas sin empanadas
            personas_vacias = []
            for nombre, ped in personas.items():
                ped.pop(sabor, None)
                if all(c == 0 for c in ped.values()):
                    personas_vacias.append(nombre)

            for nombre in personas_vacias:
                personas.pop(nombre, None)

            # --- REGENERAR lista de pedidos ya hechos ---
            pedidos_list.controls.clear()
            for p, ped in personas.items():
                detalles = [f"{s}: {c}" for s, c in ped.items() if c > 0]
                if detalles:
                    texto_detalle = ", ".join(detalles)
                else:
                    texto_detalle = "(sin pedido)"
                card = ft.Card(
                    ft.Container(
                        ft.Column([
                            ft.Text(p, size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(texto_detalle, size=16),
                        ]),
                        padding=10,
                        border=ft.border.all(1, "gray"),
                        border_radius=8,
                        width=400,
                    ),
                    margin=ft.margin.only(bottom=10),
                    elevation=2,
                )
                pedidos_list.controls.append(card)

            mostrar_sabores()
            page.update()
        check_sabores()


    def agregar_sabor(sabor):
        sabor = sabor.strip()
        if sabor and sabor not in sabores:
            sabores.append(sabor)
            conteos[sabor] = 0
            mostrar_sabores()
            check_sabores()

    def on_click_sugerido(e, sabor):
        agregar_sabor(sabor)

    # --- Botón de reset ---
    def reiniciar_pedido(e=None):
        nonlocal mostrar_por_personas, tipo_conteo_elegido, objetivo_empanadas, objetivo_personas
        conteos.clear()
        personas.clear()
        textos.clear()
        textos_persona.clear()
        pedidos_list.controls.clear()
        objetivo_empanadas = 0
        objetivo_personas = 0
        mostrar_por_personas = True
        tipo_conteo_elegido = None

        # Volver a inicializar conteos para los sabores (para que los botones sigan funcionando)
        for s in sabores:
            conteos[s] = 0

        # Mostrar pantalla de elección de modelo
        mostrar_opcion_tipo_conteo()

        # Recalcular totales desde cero (si después entra a general)
        actualizar_general()

        page.update()



    boton_reset = ft.ElevatedButton("Reiniciar pedido", on_click=reiniciar_pedido)


    # --- Popups para editar objetivos ---
    def popup_editar_valor(titulo, valor_actual, callback_confirmar):
        popup_input = ft.TextField(value=str(valor_actual), width=200)
        def confirmar(e):
            val = (popup_input.value or "").strip()
            if val.isdigit(): callback_confirmar(int(val))
            page.overlay.clear(); page.update()
        page.overlay.clear()
        page.overlay.append(ft.AlertDialog(
            title=ft.Text(titulo), content=popup_input,
            actions=[
                ft.ElevatedButton("Confirmar", on_click=confirmar),
                ft.ElevatedButton("Cancelar", on_click=lambda e: (page.overlay.clear(), page.update())),
            ],
            open=True,
        ))
        page.update()

    def set_objetivo_empanadas(v): nonlocal objetivo_empanadas; objetivo_empanadas = v
    def set_objetivo_personas(v): nonlocal objetivo_personas; objetivo_personas = v

    def boton_editar_empanadas(callback):
        return ft.ElevatedButton(
            f"Cantidad total: {objetivo_empanadas or 'Sin límite'}",
            on_click=lambda e: popup_editar_valor(
                "Editar cantidad total", objetivo_empanadas, lambda v: (set_objetivo_empanadas(v), callback())),
            width=300)

    def boton_editar_personas(callback):
        return ft.ElevatedButton(
            f"Máximo personas: {objetivo_personas or 'Sin límite'}",
            on_click=lambda e: popup_editar_valor(
                "Editar cantidad personas",
                objetivo_personas,
                lambda v: (set_objetivo_personas(v), actualizar_faltantes_personas_y_empanadas(), callback())
            ),
            width=300
        )

    # --- Pantallas para fijar cantidad ---
    def pantalla_cantidad_empanadas(callback):
        if page.controls is None:
            page.controls = []
        page.controls.clear()
        opciones = [6, 12, 24, 36]
        input_box = ft.TextField(label="Cantidad de empanadas (opcional)", width=200)

        def elegir(v): 
            input_box.value = str(v)
            callback(v)

        def continuar(e):
            valor = (input_box.value or "").strip()
            callback(int(valor) if valor.isdigit() else 0)

        page.add(ft.Column([
            ft.Text(
                "¿Querés fijar cantidad total de empanadas?",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Row([ft.ElevatedButton(str(v), on_click=lambda e, v=v: elegir(v)) for v in opciones],
                alignment=ft.MainAxisAlignment.CENTER),
            input_box,
            ft.ElevatedButton("Continuar", on_click=continuar),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, expand=True))


    def pantalla_cantidad_personas(callback):
        if page.controls is None:
            page.controls = []
        page.controls.clear()
        input_box = ft.TextField(label="Cantidad de personas (opcional)", width=200)

        def continuar(e):
            valor = (input_box.value or "").strip()
            callback(int(valor) if valor.isdigit() else 0)

        page.add(ft.Column([
            ft.Text(
                "¿Querés fijar cantidad máxima de personas?",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            input_box,
            ft.ElevatedButton("Continuar", on_click=continuar),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))

    total_text, faltan_text = ft.Text(size=24, weight=ft.FontWeight.BOLD), ft.Text(size=20, italic=True)
    
    def actualizar_general():
        total = sum(conteos.values())
        total_text.value = f"Total: {total}"
        if objetivo_empanadas:
            diff = objetivo_empanadas - total
            faltan_text.value = f"Faltan: {diff}" if diff >= 0 else f"Te pasaste por: {abs(diff)}"
        else:
            faltan_text.value = ""
        for s, t in textos.items():
            t.value = f"{s}: {conteos[s]}"
        page.update()
    
    def sumar_general(s): conteos[s]+=1; actualizar_general()
    
    def restar_general(s):
        if conteos[s]>0: conteos[s]-=1; actualizar_general()

    def elegir_tipo_conteo(tipo):
        nonlocal tipo_conteo_elegido, ya_pregunto_empanadas, ya_pregunto_personas
        tipo_conteo_elegido = tipo

        if tipo == "persona":
            # Preguntar solo si nunca se preguntó Y no hay objetivo de personas ya definido
            if not ya_pregunto_personas and objetivo_personas == 0:
                ya_pregunto_personas = True
                pantalla_cantidad_personas(lambda v: (
                    set_objetivo_personas(v),
                    # Luego preguntar empanadas (solo si no se preguntó antes y no está fijado)
                    (pantalla_cantidad_empanadas(lambda x: (
                        set_objetivo_empanadas(x),
                        mostrar_contador_persona()
                    )) if not ya_pregunto_empanadas and objetivo_empanadas == 0 else mostrar_contador_persona())
                ))
            else:
                mostrar_contador_persona()
        else:
            # Para el modo general: solo preguntar empanadas si nunca se hizo y no está fijado
            if not ya_pregunto_empanadas and objetivo_empanadas == 0:
                ya_pregunto_empanadas = True
                pantalla_cantidad_empanadas(lambda x: (
                    set_objetivo_empanadas(x),
                    mostrar_contador_general()
                ))
            else:
                mostrar_contador_general()


    def mostrar_contador_general():
        # Sincronizar conteos sumando desde personas
        for s in sabores:
            conteos[s] = 0
        for ped in personas.values():
            for s, c in ped.items():
                conteos[s] += c

        if page.controls is None:
            page.controls = []
        page.controls.clear()
        textos.clear()
        filas = []
        for s in sabores:
            textos[s] = ft.Text(f"{s}: 0", size=20)
            filas.append(ft.Row([
                textos[s],
                ft.IconButton(icon="remove", on_click=lambda e, s=s: restar_general(s)),
                ft.IconButton(icon="add", on_click=lambda e, s=s: sumar_general(s))],
                alignment=ft.MainAxisAlignment.CENTER, spacing=20))

        def volver_a_eleccion(e):
            nonlocal tipo_conteo_elegido
            tipo_conteo_elegido = None
            mostrar_opcion_tipo_conteo()

        page.add(ft.Column([
            boton_editar_empanadas(mostrar_contador_general),
            ft.Column(filas, spacing=10),
            total_text, faltan_text,
            ft.ElevatedButton("Ver pedido", on_click=lambda e: mostrar_resumen_general()),
            boton_reset,
            ft.ElevatedButton("Volver", on_click=volver_a_eleccion)
        ],
        alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))
        actualizar_general()


    def mostrar_resumen_general():
        if page.controls is None:
            page.controls = []
        page.controls.clear()
        # Mostrar solo sabores con cantidad > 0
        resumen = ft.Column([ft.Text(f"{s}: {c}", size=18) for s, c in conteos.items() if c > 0], spacing=5)
        total = sum(conteos.values())
        page.add(ft.Column([
            ft.Text("Tu pedido", size=24, weight=ft.FontWeight.BOLD),
            ft.Column(
                [ft.Text(f"{s}: {c}", size=18) for s, c in conteos.items() if c > 0], 
                spacing=5,
                height=400,
                scroll=ft.ScrollMode.AUTO
            ),
            ft.Text(f"Total: {total}", size=20, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton("Volver", on_click=lambda e: mostrar_contador_general())
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15))

    nombre_input = ft.TextField(label="Nombre", width=250)
    pedidos_list = ft.Column(spacing=10)
    faltan_personas_text = ft.Text(size=18, italic=True)
    faltan_empanadas_text = ft.Text(size=18, italic=True)
    boton_confirmar_persona = ft.ElevatedButton("Confirmar pedido", disabled=True)

    def editar_pedido(persona):
        # Cargar los datos actuales de esa persona
        pedido_actual = personas.get(persona, {s: 0 for s in sabores})
        campos = {}

        # Crear un formulario para modificar cantidades
        def guardar_cambios(e):
            for s in sabores:
                val = campos[s].value
                personas[persona][s] = int(val) if val.isdigit() else 0
            page.overlay.clear()
            actualizar_lista_pedidos()
            page.update()

        # Armar inputs para cada sabor
        campos_list = []
        for s in sabores:
            campos[s] = ft.TextField(
                label=s,
                value=str(pedido_actual.get(s, 0)),
                width=150
            )
            campos_list.append(campos[s])

        dialogo = ft.AlertDialog(
            title=ft.Text(f"Editar pedido de {persona}", text_align=ft.TextAlign.CENTER),
            content=ft.Column(campos_list, scroll=ft.ScrollMode.AUTO, height=300, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.ElevatedButton("Guardar", on_click=guardar_cambios),
                ft.ElevatedButton("Cancelar", on_click=lambda e: (page.overlay.clear(), page.update()))
            ],
            open=True
        )
        page.overlay.clear()
        page.overlay.append(dialogo)
        page.update()


    def chequear_confirmar_persona(e=None):
        total = sum(int(textos_persona[s].value) for s in sabores)
        boton_confirmar_persona.disabled = not (nombre_input.value or "").strip() or total == 0
        page.update()

    def sumar_persona(s):
        textos_persona[s].value = str(int(textos_persona[s].value)+1)
        chequear_confirmar_persona()
    def restar_persona(s):
        if int(textos_persona[s].value)>0:
            textos_persona[s].value = str(int(textos_persona[s].value)-1)
        chequear_confirmar_persona()

    def actualizar_faltantes_personas_y_empanadas():
        total_personas = len(personas)
        total_empanadas = sum(sum(ped.values()) for ped in personas.values())

        if objetivo_personas:
            diff_p = objetivo_personas - total_personas
            if diff_p > 1:
                faltan_personas_text.value = f"Faltan {diff_p} personas."
            elif diff_p == 1:
                faltan_personas_text.value = "Falta UNA sola persona."
            elif diff_p == 0:
                faltan_personas_text.value = "Cantidad de personas completada."
            else:
                faltan_personas_text.value = f"Agregaste {abs(diff_p)} personas de más."
        else:
            faltan_personas_text.value = ""

        if objetivo_empanadas:
            diff_e = objetivo_empanadas - total_empanadas
            if diff_e >= 0:
                faltan_empanadas_text.value = f"Faltan {diff_e} empanadas."
            else:
                faltan_empanadas_text.value = f"Te pasaste por {abs(diff_e)} empanadas."
        else:
            faltan_empanadas_text.value = ""

        page.update()

    def actualizar_lista_pedidos():
        pedidos_list.controls.clear()
        for p, ped in personas.items():
            detalles = [f"{s}: {c}" for s, c in ped.items() if c > 0]
            texto_detalle = ", ".join(detalles) if detalles else "(sin pedido)"
            pedidos_list.controls.append(
                ft.Card(
                    ft.Container(
                        ft.Column([
                            ft.Text(p, size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(texto_detalle, size=16),
                            ft.ElevatedButton("Editar", on_click=lambda e, persona=p: editar_pedido(persona))
                        ]),
                        padding=10,
                        border=ft.border.all(1, "gray"),
                        border_radius=8,
                        width=400,
                    ),
                    margin=ft.margin.only(bottom=10),
                    elevation=2,
                )
            )
        page.update()

    def confirmar_persona(e):
        nombre = (nombre_input.value or "").strip()
        if not nombre:
            return
        if nombre not in personas:
            personas[nombre] = {s:0 for s in sabores}
        for s in sabores:
            personas[nombre][s] += int(textos_persona[s].value)
            textos_persona[s].value = "0"
        nombre_input.value = ""

        def editar_pedido_persona(e, nombre):
            # Cargar valores actuales de esa persona
            for s in sabores:
                textos_persona[s].value = str(personas[nombre].get(s, 0))
            nombre_input.value = nombre
            boton_confirmar_persona.text = "Guardar cambios"

            def guardar_cambios(e):
                for s in sabores:
                    personas[nombre][s] = int(textos_persona[s].value)
                    textos_persona[s].value = "0"
                boton_confirmar_persona.text = "Confirmar pedido"
                nombre_input.value = ""
                boton_confirmar_persona.on_click = confirmar_persona
                mostrar_contador_persona()
                page.update()

            boton_confirmar_persona.on_click = guardar_cambios
            mostrar_contador_persona()
            page.update()

            # Ahora reconstruimos la lista con botón Editar
            pedidos_list.controls = []
            for p, ped in personas.items():
                detalles = [f"{s}: {c}" for s, c in ped.items() if c > 0]
                texto_detalle = ", ".join(detalles) if detalles else "(sin pedido)"
                card = ft.Card(
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text(p, size=20, weight=ft.FontWeight.BOLD),
                                ft.Text(texto_detalle, size=16),
                            ]),
                            ft.ElevatedButton("Editar", on_click=lambda e, nombre=p: editar_pedido_persona(e, nombre)),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.all(1, "gray"),
                        border_radius=8,
                        width=400,
                    ),
                    margin=ft.margin.only(bottom=10),
                    elevation=2,
                )
                pedidos_list.controls.append(card)

        actualizar_lista_pedidos()
        chequear_confirmar_persona()
        actualizar_faltantes_personas_y_empanadas()
        page.update()

    boton_confirmar_persona.on_click = confirmar_persona

    def mostrar_resumen_personas():
        nonlocal mostrar_por_personas
        if page.controls is None:
            page.controls = []
        page.controls.clear()

        total = sum(sum(ped.values()) for ped in personas.values())

        def toggle_vista(e):
            nonlocal mostrar_por_personas
            mostrar_por_personas = not mostrar_por_personas
            mostrar_resumen_personas()

        if mostrar_por_personas:
            listado = []
            for p, ped in personas.items():
                detalles = [f"{s}: {c}" for s, c in ped.items() if c > 0]
                if detalles:  # Solo mostrar personas con pedido > 0
                    texto_detalle = ", ".join(detalles)
                    listado.append(
                        ft.Card(
                            ft.Container(
                                ft.Column([
                                    ft.Text(p, size=20, weight=ft.FontWeight.BOLD),
                                    ft.Text(texto_detalle, size=16),
                                ]),
                                padding=10,
                                border=ft.border.all(1, "gray"),
                                border_radius=8,
                            ),
                            margin=ft.margin.only(bottom=10),
                            elevation=2,
                        )
                    )
            contenido = ft.Column(listado, scroll=ft.ScrollMode.AUTO, height=400, spacing=5)
            titulo = "Tu pedido (por persona)"
        else:
            gustos_totales = {s: 0 for s in sabores}
            for ped in personas.values():
                for s, c in ped.items():
                    gustos_totales[s] += c
            # Mostrar solo sabores con cantidad > 0
            listado = [ft.Text(f"{s}: {c}", size=18) for s, c in gustos_totales.items() if c > 0]
            contenido = ft.Column(listado, scroll=ft.ScrollMode.AUTO, height=400, spacing=5)
            titulo = "Tu pedido (por gustos)"

        faltan_text = ""
        if objetivo_empanadas:
            diff_e = objetivo_empanadas - total
            if diff_e >= 0:
                faltan_text = f"Faltan {diff_e} empanadas."
            else:
                faltan_text = f"Te pasaste por {abs(diff_e)} empanadas."

        page.add(ft.Column([
            ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD),
            contenido,
            ft.Text(f"Total: {total} empanadas", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(faltan_text, size=18, italic=True),
            ft.Row([
                ft.ElevatedButton(
                    "Ver por gustos" if mostrar_por_personas else "Ver por personas",
                    on_click=toggle_vista),
                ft.ElevatedButton("Volver", on_click=lambda e: mostrar_contador_persona()),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    def mostrar_contador_persona():
        if page.controls is None:
            page.controls = []
        page.controls.clear()
        textos_persona.clear()

        # --- Controles para sumar/restar empanadas por persona ---
        filas = []
        for s in sabores:
            textos_persona[s] = ft.Text("0", size=20)
            filas.append(
                ft.Row([
                    ft.Text(s, size=18),
                    ft.IconButton(icon="remove", on_click=lambda e, x=s: restar_persona(x)),
                    textos_persona[s],
                    ft.IconButton(icon="add", on_click=lambda e, x=s: sumar_persona(x))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
            )

        actualizar_faltantes_personas_y_empanadas()

        # --- Botón para volver al menú de elección ---
        def resetear_tipo_conteo_y_volver(e):
            nonlocal tipo_conteo_elegido
            tipo_conteo_elegido = None
            mostrar_opcion_tipo_conteo()

        # --- Función para actualizar pedidos en pantalla ---
        def actualizar_pedidos_list():
            pedidos_list.controls.clear()
            for p, ped in personas.items():
                detalles = [f"{s}: {c}" for s, c in ped.items() if c > 0]
                texto_detalle = ", ".join(detalles) if detalles else "(sin pedido)"
                card = ft.Card(
                    ft.Container(
                        ft.Column([
                            ft.Text(p, size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(texto_detalle, size=16),
                            ft.ElevatedButton("Editar", on_click=lambda e, persona=p: editar_pedido(persona))
                        ]),
                        padding=10,
                        border=ft.border.all(1, "gray"),
                        border_radius=8,
                        width=400,
                    ),
                    margin=ft.margin.only(bottom=10),
                    elevation=2,
                )
                pedidos_list.controls.append(card)
            page.update()

        # --- Armar la pantalla ---
        page.add(ft.Column([
            boton_editar_personas(mostrar_contador_persona),
            boton_editar_empanadas(mostrar_contador_persona),
            nombre_input,
            ft.Column(filas, spacing=10),
            boton_confirmar_persona,
            faltan_personas_text,
            faltan_empanadas_text,
            ft.ElevatedButton("Ver pedido", on_click=lambda e: mostrar_resumen_personas()),
            ft.Text("Pedidos agregados:", size=20, weight=ft.FontWeight.BOLD),
            pedidos_list,
            boton_reset,
            ft.ElevatedButton("Volver", on_click=resetear_tipo_conteo_y_volver)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.ALWAYS))

        # --- Cargar pedidos existentes al entrar ---
        actualizar_pedidos_list()

        actualizar_faltantes_personas_y_empanadas()

    def mostrar_opcion_tipo_conteo():
        nonlocal tipo_conteo_elegido

        # Si todavía no hay sabores, volver a la pantalla inicial
        if not sabores:
            # Mostrar popup en lugar de reiniciar la pantalla (evita recursión infinita)
            page.overlay.clear()
            page.overlay.append(ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Agregá al menos un sabor antes de continuar."),
                actions=[
                    ft.ElevatedButton("Ok", on_click=lambda e: (page.overlay.clear(), page.update()))
                ],
                open=True
            ))
            page.update()
            return
        
        if tipo_conteo_elegido == "persona":
            mostrar_contador_persona()
            return
        elif tipo_conteo_elegido == "general":
            mostrar_contador_general()
            return

        if page.controls is None:
            page.controls = []
        page.controls.clear()
        page.add(ft.Column([
            ft.Text("¿Querés contar por persona o general?", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Row([
                ft.ElevatedButton("Por persona", width=150, height=150, on_click=lambda e: elegir_tipo_conteo("persona")),
                ft.ElevatedButton("General", width=150, height=150, on_click=lambda e: elegir_tipo_conteo("general")),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=40),
            ft.ElevatedButton(
                "Modificar menú",
                on_click=lambda e: mostrar_pantalla_inicial(),
                width=200
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=40))

    sabor_input = ft.TextField(
        label="Agregar sabor de empanada",
        width=250,
        on_change=lambda e: actualizar_agregar()
    )
    btn_agregar = ft.ElevatedButton(
        "Agregar sabor",
        disabled=True,
        on_click=lambda e: agregar_sabor_manual(e)
    )


    # --- Pantalla inicial con sabores ---
    def mostrar_pantalla_inicial():
        if page.controls is None:
            page.controls = []
        page.controls.clear()
        sugeridos_botones = [ft.ElevatedButton(sabor, on_click=lambda e, sabor=sabor: on_click_sugerido(e, sabor)) for sabor in sabores_sugeridos]
        page.add(ft.Column([
            ft.Text("Agregá los sabores que querés", size=24, weight=ft.FontWeight.BOLD),
            sabor_input,
            btn_agregar,
            ft.Text("Sabores sugeridos:", size=18, weight=ft.FontWeight.BOLD),
            ft.Row(sugeridos_botones, spacing=8, wrap=True),
            ft.Text("Sabores agregados:", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(sabores_list, padding=5, border=ft.border.all(0.5, "gray"), border_radius=5, width=400, height=170),
            btn_confirmar_sabores,
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, expand=True))

        actualizar_agregar()
        check_sabores()

    # --- Mostrar la pantalla inicial al inicio ---
    mostrar_pantalla_inicial()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)


