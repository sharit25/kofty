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
        color = data.get("color")
        pos = data.get("pos")

        var = f"__w{widget_counter}__"
        widget_counter += 1

        if wtype == "Button":
            output.append(f'{var} = gui_add_button("{text}", {parent_expr})')
        elif wtype == "Label":
            output.append(f'{var} = gui_add_label("{text}", {parent_expr})')
        else:
            raise ValueError(f"Unknown widget type: {wtype}")

        if size is not None:
            sv = size.split("#")[0]
            parts = [p.strip().replace("dp", "") for p in sv.split(",")]
            if len(parts) >= 2:
                output.append(f"gui_set_size({var}, {parts[0]}, {parts[1]})")

        if color is not None:
            cv = color.split("#")[0]
            parts = [p.strip() for p in cv.split(",")]
            if len(parts) >= 3:
                if wtype == "Button":
                    output.append(
                        f"gui_set_button_color({var}, {parts[0]}, {parts[1]}, {parts[2]})"
                    )
                else:
                    output.append(
                        f"gui_set_label_color({var}, {parts[0]}, {parts[1]}, {parts[2]})"
                    )

        if pos is not None:
            pv = pos.split("#")[0]
            parts = [p.strip() for p in pv.split(",")]
            if len(parts) >= 2:
                output.append(f"gui_set_pos({var}, {parts[0]}, {parts[1]})")

        current_widget_type = None
        current_widget_data = {}

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            output.append(line)
            continue

        # 1) <BoxLayout>: or <GridLayout>:
        m = re.match(r"^<(BoxLayout|GridLayout)>:$", stripped)
        if m:
            flush_widget()
            kind = m.group(1)
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
                    output.append(
                        f"{var} = gui_add_boxlayout({orient}, 5, {parent})"
                    )
                    stack.append(("BoxLayout", var))
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

            if current_widget_type is not None:
                current_widget_data[key] = value
                continue

        output.append(line)

    flush_widget()
    return "\n".join(output)


def load_ui_file(filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as f:
        return parse_kv_syntax(f.read())
