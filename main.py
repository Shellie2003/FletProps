import flet as ft
from flet import Icons, Colors
import json
import os


# --- DICTIONNAIRE DE DÉFINITIONS ---
PROPERTY_DOCS = {
    "width": "Largeur du contrôle. Si infini, remplit l'espace.",
    "height": "Hauteur du contrôle.",
    "visible": "Affiche ou cache le contrôle.",
    "disabled": "Désactive les interactions (clics).",
    "opacity": "Transparence (0.0 à 1.0).",
    "rotate": "Rotation en radians.",
    "scale": "Facteur d'agrandissement.",
    "offset": "Décalage (x, y) visuel.",
    "expand": "Remplit l'espace disponible (Flex).",
    "bgcolor": "Couleur de fond.",
    "color": "Couleur du texte ou de l'icône.",
    "padding": "Espace intérieur.",
    "margin": "Espace extérieur.",
    "alignment": "Position du contenu (ex: center).",
    "shape": "Forme géométrique (ex: BoxShape.CIRCLE).",
    "border_radius": "Arrondi des angles.",
    "border": "Bordure (épaisseur, couleur).",
    "shadow": "Ombre portée.",
    "clip_behavior": "Méthode de découpage du contenu qui dépasse.",
    "on_click": "Événement au clic.",
    "data": "Données arbitraires attachées.",
    "tooltip": "Texte d'aide au survol.",
    "adaptive": "S'adapte au style iOS/Android automatiquement.",
    "content": "Le contenu enfant de ce contrôle.",
    "title": "Titre affiché dans le contrôle.",
    "actions": "Liste des boutons d'action (souvent en bas).",
    "open": "Définit si le dialogue est ouvert ou fermé.",
}


# --- COULEURS THÈME ---
COLORS = {
    'light': {
        'bg': '#F8F9FA',
        'card': '#FFFFFF',
        'text': '#1A1A1A',
        'subtext': '#6C757D',
        'primary': '#007AFF',
        'border': '#E9ECEF',
        'codebg': '#F1F3F5',
        'accent': '#5E5CE6',
        'success': '#34C759'
    },
    'dark': {
        'bg': '#000000',
        'card': '#1C1C1E',
        'text': '#FFFFFF',
        'subtext': '#A1A1AA',
        'primary': '#0A84FF',
        'border': '#2C2C2E',
        'codebg': '#2C2C2E',
        'accent': '#5E5CE6',
        'success': '#30D158'
    }
}


def main(page: ft.Page):
    # Configuration de la page
    page.title = "JSON Docs Viewer"
    page.padding = 0
    page.spacing = 0
    
    # --- ÉTAT DE L'APPLICATION ---
    json_data = {}
    current_key = None
    theme_mode = 'light'
    favorites = []
    drawer_search_query = ""
    appbar_search_query = ""
    search_mode = False
    
    def get_theme():
        return COLORS[theme_mode]
    
    def apply_theme():
        theme = get_theme()
        page.bgcolor = theme['bg']
        page.theme_mode = ft.ThemeMode.LIGHT if theme_mode == 'light' else ft.ThemeMode.DARK
        page.update()
    
    # --- GESTION DES FAVORIS ---
    def load_favorites():
        nonlocal favorites
        try:
            if os.path.exists('favorites.json'):
                with open('favorites.json', 'r') as f:
                    favorites = json.load(f)
        except Exception:
            favorites = []
    
    def save_favorites():
        try:
            with open('favorites.json', 'w') as f:
                json.dump(favorites, f)
        except Exception:
            pass
    
    def toggle_favorite(key):
        nonlocal favorites
        if key in favorites:
            favorites.remove(key)
        else:
            favorites.append(key)
        save_favorites()
        render_content()
    
    # --- GESTION DU FICHIER ---
    def pick_file_result(e: ft.FilePickerResultEvent):
        nonlocal json_data, current_key
        if e.files:
            try:
                with open(e.files[0].path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                keys = sorted(json_data.keys())
                if keys:
                    current_key = keys[0]
                
                page.open(ft.SnackBar(
                    content=ft.Text("Fichier chargé avec succès!"),
                    bgcolor=get_theme()['success']
                ))
                render_content()
                update_nav_bar()
                open_drawer()
            except Exception as ex:
                page.open(ft.SnackBar(
                    content=ft.Text(f"Erreur: {str(ex)}"),
                    bgcolor=Colors.RED_400
                ))
        page.update()
    
    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)
    
    # --- COPIER LE CODE ---
    def copy_code(description):
        import re
        match = re.search(r'```python\s*([\s\S]*?)```', description)
        if match and match.group(1):
            page.set_clipboard(match.group(1).strip())
            page.open(ft.SnackBar(
                content=ft.Text("Code copié!"),
                bgcolor=get_theme()['success']
            ))
            page.update()
    
    # --- DRAWER (BIBLIOTHÈQUE) ---
    drawer_ref = ft.Ref[ft.NavigationDrawer]()
    
    def filter_drawer_keys():
        if not json_data:
            return []
        
        all_keys = sorted(json_data.keys())
        
        # Filtrer par recherche
        if drawer_search_query:
            all_keys = [k for k in all_keys if drawer_search_query.lower() in k.lower()]
        
        # Trier par favoris
        all_keys.sort(key=lambda k: (k not in favorites, k))
        return all_keys
    
    def on_drawer_search_change(e):
        nonlocal drawer_search_query
        drawer_search_query = e.control.value
        update_drawer_items()
    
    def update_drawer_items():
        if drawer_ref.current:
            filtered = filter_drawer_keys()
            theme = get_theme()
            
            drawer_ref.current.controls = [
                # En-tête
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            "Bibliothèque",
                            size=22,
                            weight=ft.FontWeight.W_800,
                            color=theme['text']
                        ),
                        ft.IconButton(
                            icon=Icons.CLOSE,
                            icon_color=theme['subtext'],
                            on_click=close_drawer
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=20,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, theme['border']))
                ),
                
                # Barre de recherche
                ft.Container(
                    content=ft.TextField(
                        hint_text="Rechercher...",
                        prefix_icon=Icons.SEARCH,
                        border_color=Colors.TRANSPARENT,
                        bgcolor=theme['codebg'],
                        color=theme['text'],
                        on_change=on_drawer_search_change,
                        value=drawer_search_query
                    ),
                    padding=ft.padding.symmetric(15, 10)
                ),
                
                # Liste des items
                ft.Container(
                    content=ft.Column(
                        controls=[
                            create_drawer_item(key)
                            for key in filtered
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0
                    ),
                    expand=True
                )
            ]
            page.update()
    
    def create_drawer_item(key):
        theme = get_theme()
        is_fav = key in favorites
        is_active = current_key == key
        
        def select_item(e):
            nonlocal current_key
            current_key = key
            close_drawer()
            render_content()
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    Icons.STAR,
                    color="#FFD700",
                    size=14,
                    visible=is_fav
                ),
                ft.Text(
                    key,
                    color=theme['primary'] if is_active else theme['text'],
                    weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_400,
                    size=16
                )
            ], spacing=8),
            padding=ft.padding.symmetric(20, 16),
            on_click=select_item,
            bgcolor=theme['codebg'] if is_active else None,
            border=ft.border.only(
                left=ft.border.BorderSide(4, theme['primary'])
            ) if is_active else None
        )
    
    def open_drawer():
        if drawer_ref.current and json_data:
            update_drawer_items()
            drawer_ref.current.open = True
            page.update()
    
    def close_drawer(e=None):
        if drawer_ref.current:
            drawer_ref.current.open = False
            page.update()
    
    # --- TOGGLE THÈME ---
    def toggle_theme(e):
        nonlocal theme_mode
        theme_mode = 'dark' if theme_mode == 'light' else 'light'
        apply_theme()
        render_content()
        update_nav_bar()
    
    # --- RECHERCHE DANS L'APPBAR ---
    def toggle_search_mode(e):
        nonlocal search_mode
        search_mode = not search_mode
        update_nav_bar()
    
    def on_appbar_search_change(e):
        nonlocal appbar_search_query, current_key
        appbar_search_query = e.control.value.lower()
        
        if not json_data:
            return
        
        # Filtrer les clés
        filtered_keys = [k for k in json_data.keys() if appbar_search_query in k.lower()]
        
        if filtered_keys:
            # Trier et sélectionner la première
            filtered_keys.sort()
            current_key = filtered_keys[0]
            render_content()
    
    def clear_appbar_search(e):
        nonlocal appbar_search_query, search_mode
        appbar_search_query = ""
        search_mode = False
        update_nav_bar()
        if json_data and current_key:
            render_content()
    
    # --- RENDU DU CONTENU ---
    content_column = ft.Column(
        spacing=0,
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )
    
    def render_empty_state():
        theme = get_theme()
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(
                        Icons.CLOUD_UPLOAD_OUTLINED,
                        size=40,
                        color=theme['primary']
                    ),
                    width=80,
                    height=80,
                    bgcolor=theme['codebg'],
                    border_radius=40,
                    alignment=ft.alignment.center
                ),
                ft.Text(
                    "Aucun fichier chargé",
                    size=20,
                    weight=ft.FontWeight.W_700,
                    color=theme['text']
                ),
                ft.ElevatedButton(
                    "Ouvrir un fichier JSON",
                    bgcolor=theme['primary'],
                    color="#FFFFFF",
                    on_click=lambda _: file_picker.pick_files(
                        allowed_extensions=["json"]
                    ),
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(30, 15),
                        shape=ft.RoundedRectangleBorder(radius=30)
                    )
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20),
            expand=True,
            alignment=ft.alignment.center
        )
    
    def render_property_row(key, val, is_last):
        theme = get_theme()
        explanation = val.get('description') or PROPERTY_DOCS.get(key)
        
        prop_container = ft.Column([
            # En-tête de propriété
            ft.Row([
                ft.Text(
                    key,
                    size=16,
                    weight=ft.FontWeight.W_700,
                    color=theme['text']
                ),
                ft.Container(
                    content=ft.Text(
                        "REQ",
                        size=10,
                        weight=ft.FontWeight.W_800,
                        color="#FFFFFF"
                    ),
                    bgcolor="#FF3B30",
                    padding=ft.padding.symmetric(6, 2),
                    border_radius=4,
                    visible=val.get('required', False)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Détails
            ft.Column([
                ft.Text(
                    val.get('type', 'unknown'),
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=theme['accent']
                ),
                ft.Text(
                    f"Défaut: {val.get('default', 'null')}",
                    size=13,
                    color=theme['subtext']
                )
            ], spacing=4),
            
            # Explication
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        Icons.INFO_OUTLINE,
                        size=14,
                        color=theme['primary']
                    ),
                    ft.Text(
                        explanation,
                        size=12,
                        color=theme['subtext'],
                        italic=True,
                        expand=True
                    )
                ], spacing=6),
                bgcolor=theme['codebg'],
                padding=8,
                border_radius=6,
                visible=explanation is not None
            )
        ], spacing=8)
        
        return ft.Container(
            content=prop_container,
            padding=ft.padding.symmetric(20, 16),
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, theme['border'])
            ) if not is_last else None
        )
    
    def render_detail_view():
        theme = get_theme()
        item = json_data[current_key]
        has_code = '```python' in item.get('description', '')
        is_fav = current_key in favorites
        
        children = [
            # En-tête
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(
                            current_key,
                            size=30,
                            weight=ft.FontWeight.W_800,
                            color=theme['text']
                        ),
                        ft.Text(
                            "COMPONENT",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=theme['accent']
                        )
                    ], spacing=4, expand=True),
                    ft.IconButton(
                        icon=Icons.STAR if is_fav else Icons.STAR_OUTLINE,
                        icon_color="#FFD700" if is_fav else theme['subtext'],
                        icon_size=28,
                        on_click=lambda _: toggle_favorite(current_key)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(20, 20)
            ),
            
            # Actions
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "Copier l'exemple",
                        icon=Icons.COPY_OUTLINED,
                        bgcolor=theme['success'],
                        color="#FFFFFF",
                        on_click=lambda _: copy_code(item.get('description', '')),
                        
                    )
                ], spacing=10),
                padding=ft.padding.symmetric(24, 0)
            ) if has_code else ft.Container(height=0),
            
            # Description
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "DESCRIPTION",
                        size=12,
                        weight=ft.FontWeight.W_700,
                        color=theme['subtext']
                    ),
                    ft.Markdown(
                        item.get('description', '_Aucune description_'),
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK
                    )
                ], spacing=15),
                bgcolor=theme['card'],
                padding=20,
                border_radius=16,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=Colors.with_opacity(0.1, theme['text']),
                    offset=ft.Offset(0, 4)
                ),
                margin=ft.margin.symmetric(20, 0)
            ),
            
            # Propriétés
            ft.Container(
                content=ft.Text(
                    "Propriétés",
                    size=20,
                    weight=ft.FontWeight.W_700,
                    color=theme['text']
                ),
                padding=ft.padding.only(20, 20, 20, 15)
            )
        ]
        
        # Ajouter les propriétés
        if item.get('properties'):
            props = list(item['properties'].items())
            children.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            render_property_row(key, val, i == len(props) - 1)
                            for i, (key, val) in enumerate(props)
                        ],
                        spacing=0
                    ),
                    bgcolor=theme['card'],
                    border_radius=16,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=Colors.with_opacity(0.1, theme['text']),
                        offset=ft.Offset(0, 4)
                    ),
                    margin=ft.margin.symmetric(20, 0),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            )
        else:
            children.append(
                ft.Container(
                    content=ft.Text(
                        "Aucune propriété.",
                        size=14,
                        color=theme['subtext'],
                        italic=True
                    ),
                    padding=ft.padding.symmetric(20, 10)
                )
            )
        
        # Espace en bas
        children.append(ft.Container(height=50))
        
        return ft.Column(
            controls=children,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def render_content():
        theme = get_theme()
        content_column.controls.clear()
        
        if not json_data or not current_key:
            content_column.controls.append(render_empty_state())
        else:
            content_column.controls.append(render_detail_view())
        
        page.update()
    
    # --- BARRE DE NAVIGATION ---
    nav_bar_ref = ft.Ref[ft.Container]()
    
    def update_nav_bar():
        theme = get_theme()
        
        if search_mode:
            # Mode recherche
            nav_bar_ref.current.content = ft.Row([
                ft.IconButton(
                    icon=Icons.ARROW_BACK,
                    icon_size=24,
                    on_click=clear_appbar_search
                ),
                ft.TextField(
                    hint_text="Rechercher un composant...",
                    border_color=Colors.TRANSPARENT,
                    bgcolor=theme['codebg'],
                    color=theme['text'],
                    on_change=on_appbar_search_change,
                    value=appbar_search_query,
                    autofocus=True,
                    expand=True,
                    text_size=16
                ),
                ft.IconButton(
                    icon=Icons.CLOSE,
                    icon_size=22,
                    on_click=clear_appbar_search,
                    visible=bool(appbar_search_query)
                )
            ], spacing=10)
        else:
            # Mode normal
            nav_bar_ref.current.content = ft.Row([
                ft.IconButton(
                    icon=Icons.LIST,
                    icon_size=24,
                    on_click=lambda _: open_drawer(),
                    disabled=not json_data
                ),
                ft.Text(
                    "JSON Docs",
                    size=17,
                    weight=ft.FontWeight.W_700,
                    expand=True,
                    color=theme['text']
                ),
                ft.IconButton(
                    icon=Icons.SEARCH,
                    icon_size=24,
                    on_click=toggle_search_mode,
                    disabled=not json_data
                ),
                ft.IconButton(
                    icon=Icons.NIGHTLIGHT_ROUND if theme_mode == 'light' else Icons.WB_SUNNY,
                    icon_size=22,
                    on_click=toggle_theme
                ),
                ft.IconButton(
                    icon=Icons.FOLDER_OPEN_OUTLINED,
                    icon_size=24,
                    icon_color=theme['primary'],
                    on_click=lambda _: file_picker.pick_files(allowed_extensions=["json"])
                )
            ], spacing=5)
        
        page.update()
    
    nav_bar = ft.Container(
        ref=nav_bar_ref,
        content=ft.Row([]),  # Sera rempli par update_nav_bar
        padding=ft.padding.symmetric(20, 15),
        border=ft.border.only(bottom=ft.border.BorderSide(1, get_theme()['border']))
    )
    
    # --- DRAWER ---
    drawer = ft.NavigationDrawer(
        ref=drawer_ref,
        controls=[],
        bgcolor=get_theme()['bg']
    )
    
    # --- LAYOUT PRINCIPAL ---
    page.add(
        ft.Column([
            nav_bar,
            content_column
        ], spacing=0, expand=True)
    )
    
    page.drawer = drawer
    
    # Initialisation
    load_favorites()
    apply_theme()
    update_nav_bar()
    render_content()


# Point d'entrée
if __name__ == "__main__":
    ft.app(target=main)
