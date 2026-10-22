import re


def parse_kv_syntax(source: str) -> str:
    """Translate Kivy-style .kfy UI into Kofty function calls."""
    lines = source.split("\n")
    output = []

    stack = []
    current_widget_type = None
    current_widget_data = {}
    widget_counter = 0

    def flush_widget():
        nonlocal current_widget_type, current_widget_data, widget_counter
        if current_widget_type is None:
            return

        wtype = current_widget_type
        data = current_widget_data
        parent_expr = stack[-1][1] if (stack and stack[-1][1]) else "-1"
        text = data.get("text", '""').strip('"')

        size = data.get("size")
        size_hint = data.get("size_hint")
        color = data.get("color")
        bg_color = data.get("background_color")
        pos = data.get("pos")
        pos_hint = data.get("pos_hint")

        var = f"__w{widget_counter}__"
        widget_counter += 1


        if wtype == "Button":
            output.append(f'{var} = Button("{text}", {parent_expr})')
        elif wtype == "Label":
            output.append(f'{var} = Label("{text}", {parent_expr})')
        elif wtype == "TextInput":
            output.append(f'{var} = TextInput("{text}", {parent_expr})')
        else:
            raise ValueError(f"Unknown widget type: {wtype}")

        if size is not None:
            sv = size.replace('"', '').replace("dp", "").split("#")[0]
            parts = [p.strip() for p in sv.split(",")]
            if len(parts) >= 2:
                output.append(f"{var}.set_size({parts[0]}, {parts[1]})")

        if size_hint is not None:
            sh = size_hint.replace('"', '').replace("dp", "").split("#")[0]
            parts = [p.strip() for p in sh.split(",")]
            if len(parts) == 2:
                w_pct = -1.0 if parts[0].lower() == "none" else float(parts[0])
                h_pct = -1.0 if parts[1].lower() == "none" else float(parts[1])
                output.append(f"{var}.set_size_hint({w_pct}, {h_pct})")

        def parse_color_str(c_str):
            c_str = c_str.strip()
            r, g, b, a = 255, 255, 255, 255
            if c_str.startswith("#"):
                hex_val = c_str.lstrip("#")
                if len(hex_val) >= 6:
                    r = int(hex_val[0:2], 16)
                    g = int(hex_val[2:4], 16)
                    b = int(hex_val[4:6], 16)
                if len(hex_val) == 8:
                    a = int(hex_val[6:8], 16)
            else:
                cv = c_str.split("#")[0]
                parts = [float(p.strip()) for p in cv.split(",") if p.strip()]
                if len(parts) >= 3:
                    is_float = (parts[0] <= 1.0 and parts[1] <= 1.0 and parts[2] <= 1.0)
                    mult = 255.0 if is_float else 1.0
                    r = int(parts[0] * mult)
                    g = int(parts[1] * mult)
                    b = int(parts[2] * mult)
                    if len(parts) >= 4:
                        a = int(parts[3] * mult)
            return f"{r}, {g}, {b}, {a}"

        if color is not None:
            c_str = parse_color_str(color)
            if wtype == "Button":
                output.append(f"gui_set_button_text_color({var}.widget_id, {c_str})")
            else:
                output.append(f"gui_set_label_color({var}.widget_id, {c_str})")

        if bg_color is not None:
            c_str = parse_color_str(bg_color)
            if wtype == "Button":
                output.append(f"gui_set_button_bg_color({var}.widget_id, {c_str})")
            else:
                output.append(f"gui_set_label_bg_color({var}.widget_id, {c_str})")

        # Check if the parent is an AnchorLayout
        parent_is_anchor = (stack and stack[-1][0] == "AnchorLayout")
        anchor = data.get("anchor")

        if parent_is_anchor and anchor is not None:
            anchor_str = anchor.strip('"').strip("'")
            anchor_map = {
                "top-left": 0, "top-center": 1, "top-right": 2,
                "center-left": 3, "center": 4, "center-right": 5,
                "bottom-left": 6, "bottom-center": 7, "bottom-right": 8
            }
            anchor_side = anchor_map.get(anchor_str, 0)

            ox, oy = 0, 0
            if pos is not None:
                pv = pos.split("#")[0]
                parts = [p.strip() for p in pv.split(",")]
                if len(parts) >= 2:
                    ox, oy = parts[0], parts[1]

            w, h = 100, 100  # default
            if size is not None:
                sv = size.replace('"', '').replace("dp", "").split("#")[0]
                parts = [p.strip() for p in sv.split(",")]
                if len(parts) >= 2:
                    w, h = parts[0], parts[1]
            output.append(f"gui_anchor_add({parent_expr}, {var}.widget_id, {anchor_side}, {ox}, {oy}, {w}, {h})")
        else:
            if pos is not None:
                pv = pos.replace('"', '').replace("dp", "").split("#")[0]
                parts = [p.strip() for p in pv.split(",")]
                if len(parts) >= 2:
                    output.append(f"{var}.set_pos({parts[0]}, {parts[1]})")

            if pos_hint is not None:
                import json
                try:
                    ph = json.loads(pos_hint)
                    for key, value in ph.items():
                        output.append(f'{var}.set_pos_hint("{key}", {value})')
                except:
                    pass
        current_widget_type = None
        current_widget_data = {}

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            output.append(line)
            continue

        # 0) background_color (for the window / root layout)
        m = re.match(r"^background_color:\s*(.*)$", stripped)
        if m:
            if current_widget_type is None:
                # Root-level background color
                val = m.group(1).split("#")[0]
                parts = [p.strip() for p in val.split(",")]
                if len(parts) >= 3:
                    output.append(f"gui_set_window_color({parts[0]}, {parts[1]}, {parts[2]})")
                continue
        # else: it's a widget background_color, let it be handled below
        # 1) <AnyCustomWidget>:
        m = re.match(r"^<(\w+)>:$", stripped)
        if m:
            flush_widget()
            kind = m.group(1)

            # Map custom class names to their base layout types
            if "BoxLayout" in kind:
                stack.append(("BoxLayout", None))
            elif "GridLayout" in kind:
                stack.append(("GridLayout", None))
            elif "AnchorLayout" in kind:
                var = f"__layout{len(stack)}_anchor__"
                parent = stack[-1][1] if (stack and stack[-1][1]) else "-1"
                output.append(f"{var} = gui_add_anchorlayout({parent})")
                stack.append(("AnchorLayout", var))
            elif kind in ("MainWidget", "Widget"):
                stack.append(("Widget", "-1"))
            else:
                stack.append((kind, None))
            continue

        if m:
            flush_widget()
            kind = m.group(1)

            if kind == "AnchorLayout":
                # Create the AnchorLayout immediately
                var = f"__layout{len(stack)}_anchor__"
                parent = stack[-1][1] if (stack and stack[-1][1]) else "-1"
                output.append(f"{var} = gui_add_anchorlayout({parent})")
                stack.append(("AnchorLayout", var))
            else:
                stack.append((kind, None))
            continue

        # 2) Any other <ClassName>: wrapper — strip it
        if re.match(r"^<\w+>:$", stripped):
            flush_widget()
            continue

        # 3) Button: / Label:
        m = re.match(r"^(Button|Label):$", stripped)
        if m:
            flush_widget()
            current_widget_type = m.group(1)
            current_widget_data = {}
            continue

        # 4) key: value
        m = re.match(r"^(\w+):\s*(.*)$", stripped)
        if m:
            key = m.group(1)
            value = m.group(2).strip()

            if current_widget_type is None and stack:
                kind, _ = stack[-1]

                if kind == "BoxLayout" and key == "orientation":
                    orient = 0 if "vertical" in value else 1
                    stack.pop()
                    var = f"__layout{len(stack)}_box__"
                    parent = stack[-1][1] if (stack and stack[-1][1]) else "-1"
                    # Check if the next property is spacing
                    output.append(f"{var} = gui_add_boxlayout({orient}, 5, {parent})")
                    stack.append(("BoxLayout", var))
                    continue

                if kind == "BoxLayout" and key == "spacing":
                    # Find the layout variable in the stack
                    var = stack[-1][1]
                    # Replace the "5" with the spacing value in the last output line
                    if output:
                        output[-1] = output[-1].replace(", 5,", f", {value.strip()},")
                    continue
                if kind == "GridLayout" and key == "cols":
                    cols = int(value.split("#")[0])
                    stack.pop()
                    var = f"__layout{len(stack)}_grid__"
                    parent = stack[-1][1] if (stack and stack[-1][1]) else "-1"
                    output.append(
                        f"{var} = gui_add_gridlayout({cols}, 5, {parent})"
                    )
                    stack.append(("GridLayout", var))
                    continue

                if kind == "AnchorLayout":
                    stack.pop()
                    var = f"__layout{len(stack)}_anchor__"
                    parent = stack[-1][1] if (stack and stack[-1][1]) else "-1"
                    output.append(f"{var} = gui_add_anchorlayout({parent})")
                    stack.append(("AnchorLayout", var))
                    continue

            if current_widget_type is not None:
                current_widget_data[key] = value
                continue

        output.append(line)

    flush_widget()
    return "\n".join(output)


def load_ui_file(filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as f:
        return parse_kv_syntax(f.read())
